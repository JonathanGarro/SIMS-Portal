# Deploying the SIMS Portal to AWS

Everything runs from a terminal. The flow: build an image from a clean copy of `main`, push it under the commit's ID, register a new task definition revision that uses it, run any database migrations, then point the ECS service at the new revision.

| What | Where |
|---|---|
| Region | `us-east-2` |
| Image registry (ECR) | repository `simsportal`, tagged by commit (e.g. `simsportal:4298ea58`) |
| Service (ECS, Fargate, x86) | cluster `simsportal`, service `SIMSPortal`, container `flask` |
| Database (RDS, Postgres 14) | `simsportaldb` |
| App logs (CloudWatch) | log group `/ecs/simsportal` |
| Request logs (S3) | bucket `simsportal-alb-access-logs-<account ID>`, kept 1 year: CloudFront logs under `cloudfront/`, load balancer logs under `simsportal/` |

> [!NOTE] What's no longer needed
> - **No manual edits before deploying.** Debug mode follows `FLASK_DEBUG`, which production doesn't set. The Dockerfile always runs gunicorn. docker-compose is for local dev only.
> - **No Manual Refresh after deploying.** The maps read from the database (#173).
> - **No console clicking.** ECR's "View Push Commands" and ECS's "Force new deployment" are steps 2 and 6 below.
> - **`:latest` isn't used.** Production runs a commit tag, so each deploy is traceable, and rolling back means pointing at an earlier revision.

## Before you start

- Docker Desktop is running.
- You're on an up-to-date `main` with CI green: `git checkout main && git pull`.
- You're signed in to AWS: `aws login --profile sims`. If it asks to overwrite another profile, you forgot `--profile sims`.

Every command below runs from the repo root, in one terminal session. Set these first:

```bash
export AWS_PROFILE=sims AWS_REGION=us-east-2
CLUSTER=simsportal SERVICE=SIMSPortal CONTAINER=flask REPO=simsportal
ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
REGISTRY=$ACCOUNT.dkr.ecr.$AWS_REGION.amazonaws.com
SHA=$(git rev-parse --short HEAD)
CURRENT_TD=$(aws ecs describe-services --cluster $CLUSTER --services $SERVICE --query 'services[0].taskDefinition' --output text)
NETWORK=$(aws ecs describe-services --cluster $CLUSTER --services $SERVICE --query 'services[0].networkConfiguration' --output json)
echo "Deploying $SHA; production is on ${CURRENT_TD##*/}"
```

## 1. Build the image

Build from a clean export of the commit, not your working folder, so local files (logs, `.claude/`, uploads) can't end up in production.

```bash
BUILD=$(mktemp -d)
git archive HEAD flask_app | tar -x -C "$BUILD"
docker build --platform linux/amd64 -t $REPO:$SHA "$BUILD/flask_app"
rm -rf "$BUILD"

# sanity check: should print 152 or so (the site's images arrive through the static/assets symlink)
docker run --rm --platform linux/amd64 --entrypoint sh $REPO:$SHA -c 'ls /app/SIMS_Portal/static/assets/img | wc -l'
```

> [!WARNING] `--platform linux/amd64` is required
> Production runs on x86. A Mac builds ARM images by default, and an ARM image won't start on the service.

## 2. Push it

```bash
aws ecr get-login-password | docker login --username AWS --password-stdin $REGISTRY
docker tag $REPO:$SHA $REGISTRY/$REPO:$SHA
docker push $REGISTRY/$REPO:$SHA
```

This doesn't affect the running site, which uses whatever image its current task definition names.

## 3. Back up the database (when there are migrations)

Check whether this deploy includes migrations:

```bash
DEPLOYED_SHA=$(aws ecs describe-task-definition --task-definition $CURRENT_TD \
  --query "taskDefinition.containerDefinitions[?name=='$CONTAINER'].image" --output text | cut -d: -f2)
git diff --stat $DEPLOYED_SHA HEAD -- flask_app/migrations/versions
```

If anything is listed, take a snapshot first. It takes about 5–15 minutes:

```bash
SNAPSHOT=simsportaldb-pre-deploy-$(date +%F-%H%M)
aws rds create-db-snapshot --db-instance-identifier simsportaldb --db-snapshot-identifier $SNAPSHOT
aws rds wait db-snapshot-available --db-snapshot-identifier $SNAPSHOT && echo "snapshot $SNAPSHOT ready"
```

## 4. Register a new task definition revision

This copies the current revision and swaps in the new image. Production's settings (database URL, tokens) are in the task definition, so the temporary files are created readable only by you and deleted afterwards.

```bash
TMP=$(umask 077; mktemp -d)
aws ecs describe-task-definition --task-definition $CURRENT_TD --include TAGS --output json > $TMP/current.json
python3 - $TMP/current.json "$REGISTRY/$REPO:$SHA" "$CONTAINER" > $TMP/new.json <<'EOF'
import json, sys
src = json.load(open(sys.argv[1]))
td = src['taskDefinition']
for k in ('taskDefinitionArn', 'revision', 'status', 'requiresAttributes', 'compatibilities',
          'registeredAt', 'registeredBy', 'deregisteredAt'):
    td.pop(k, None)
if src.get('tags'):
    td['tags'] = src['tags']
container = next(c for c in td['containerDefinitions'] if c['name'] == sys.argv[3])
container['image'] = sys.argv[2]

# To add or change a setting, uncomment and edit:
# env = {e['name']: e['value'] for e in container.get('environment', [])}
# env['SETTING_NAME'] = 'value'
# container['environment'] = [{'name': k, 'value': v} for k, v in env.items()]

print(json.dumps(td))
EOF
NEW_TD=$(aws ecs register-task-definition --cli-input-json file://$TMP/new.json \
  --query 'taskDefinition.taskDefinitionArn' --output text)
rm -rf $TMP
echo "registered ${NEW_TD##*/}"
```

Registering only creates a revision. The site stays on the current one until step 6.

## 5. Run migrations (when there are any)

Migrations run as one-off tasks: a container from the **new** revision starts with production's settings, runs one `flask` command, and exits. Define this helper once per session:

```bash
flask_task() {
  local cmd task
  cmd=$(python3 -c 'import json, sys; print(json.dumps(["flask"] + sys.argv[1:]))' "$@")
  task=$(aws ecs run-task --cluster $CLUSTER --task-definition $NEW_TD --launch-type FARGATE \
    --network-configuration "$NETWORK" \
    --overrides "{\"containerOverrides\":[{\"name\":\"$CONTAINER\",\"command\":$cmd}]}" \
    --query 'tasks[0].taskArn' --output text)
  echo "== flask $*  (task ${task##*/})"
  aws ecs wait tasks-stopped --cluster $CLUSTER --tasks $task
  aws logs get-log-events --log-group-name /ecs/simsportal --log-stream-name ecs/$CONTAINER/${task##*/} \
    --start-from-head --query 'events[].message' --output text | tr '\t' '\n'
  echo "== exit code: $(aws ecs describe-tasks --cluster $CLUSTER --tasks $task --query 'tasks[0].containers[0].exitCode' --output text)"
}
```

Then:

```bash
flask_task db current      # where the database is now
flask_task db upgrade      # apply the new migrations
flask_task db current      # confirm it's at the new head
```

> [!WARNING] Order matters when a migration removes something
> - **Adds only** (new table, or a new column with a default): run the migration first, then deploy. The old code ignores the addition.
> - **Removes or renames** something the old code uses: deploy code that no longer uses it first, then migrate.
> - **Both** (the new code needs an addition and the old code needs what's removed): run `db upgrade` and step 6 back to back. Expect a minute or two of errors in between, so pick a quiet hour.
>
> Read the new files in `migrations/versions/` before deciding.

> [!NOTE] Avoid the top of the hour
> One-off tasks boot the full app, scheduler included. The scheduled jobs run on the hour (Eastern), so don't start a task at :59. A task that takes under a minute won't overlap a job.

## 6. Deploy

```bash
aws ecs update-service --cluster $CLUSTER --service $SERVICE --task-definition $NEW_TD --force-new-deployment \
  --query 'service.deployments[0].[taskDefinition,rolloutState]' --output text
aws ecs wait services-stable --cluster $CLUSTER --services $SERVICE && echo "stable"
```

It takes about 3 minutes: ECS starts the new task, the load balancer health-checks it, then the old task drains.

## 7. Smoke test

```bash
for p in /health / /login /about /static/assets/img/pump-brakes.gif /data/response_history.json; do
  printf "%-40s " $p; curl -s -o /dev/null -w "%{http_code}\n" https://rcrcsims.org$p
done

# errors in the new task's logs
TASK=$(aws ecs list-tasks --cluster $CLUSTER --service-name $SERVICE --query 'taskArns[0]' --output text)
aws logs filter-log-events --log-group-name /ecs/simsportal --log-stream-names ecs/$CONTAINER/${TASK##*/} \
  --filter-pattern '?ERROR ?Traceback ?Exception' --query 'events[].message' --output text
```

Then log in and click around. All the URLs should return 200, and the log check should print nothing.

## Rolling back

- **Code:** point the service back at the previous revision:
  ```bash
  aws ecs update-service --cluster $CLUSTER --service $SERVICE --task-definition $CURRENT_TD --force-new-deployment
  ```
  If you've lost `$CURRENT_TD`, list revisions with `aws ecs list-task-definitions --family-prefix simsportal --sort DESC`.
- **Database:** if the migrations removed something the old code needs, either run `flask_task db downgrade <revision>` (the migration's file says whether its downgrade restores data), or restore the snapshot to a new instance and switch `SQLALCHEMY_DATABASE_URI` to it.

## Production settings

These live in the task definition's environment. Change them with the snippet in step 4.

| Setting | Value | Notes |
|---|---|---|
| `FLASK_DEBUG` | **must not be set** | When set, debug mode turns on and the scheduler stays off. |
| `SQLALCHEMY_DATABASE_URI`, `SECRET_KEY`, Slack/Dropbox/GitHub/Maps/reCAPTCHA keys | set | |
| `PROXY_FIX_HOPS` | `1` | The load balancer is one proxy. Without it, every visitor looks like the load balancer, and they all share the per-IP login rate limits. |
| `HEARTBEAT_URL_SURGE_ALERTS`, `HEARTBEAT_URL_BADGES` | Better Stack heartbeat URLs | Pinged after the scheduled jobs. If unset, no pings are sent and Better Stack reports the jobs as down. |
| `PASSWORD_UPGRADE_DEADLINE` | optional, `YYYY-MM-DD` | Until this date, members with pre-policy passwords can choose "Remind me later". |
| `RATELIMIT_STORAGE_URI` | optional, `redis://…` | Shares rate-limit counts across gunicorn workers. The default in-memory store is per worker. |
| `ROOT_URL` | optional | Base URL for links in Slack messages. Defaults to `https://rcrcsims.org`. |

## Logs

Requests reach the app through two layers: visitors connect to **CloudFront** (distribution `E380WF4XO8LWJ7`, which serves rcrcsims.org and www.rcrcsims.org), CloudFront passes them to the **load balancer**, and the load balancer passes them to the app. Each layer has its own logs.

- **App logs (CloudWatch, `/ecs/simsportal`):** what the app printed: errors and tracebacks, scheduler messages, heartbeat results. Kept indefinitely. **They don't list individual web requests**, because gunicorn's access log is off.
- **CloudFront logs (S3, `cloudfront/`):** one line per visitor request, with the **visitor's real IP address**, time, method, path, query string, status code, user agent and referrer. Start here when you need to know who made a request.
- **Load balancer logs (S3, `simsportal/`):** one line per request that reached the load balancer, with status codes and timings for the app itself. The client IP here is a **CloudFront server, not the visitor**, because every request arrives through CloudFront.

Both request logs were turned on November 24, 2026, so there's nothing from before then. They share one private bucket, and a lifecycle rule deletes files after a year. CloudFront delivers files every few minutes; the load balancer every 5 minutes.

The app's own activity log (the Log table, shown under Admin → Activity Logs) is a third place to look for job results.

### Searching the request logs

Both logs are in one bucket. Look it up from the load balancer:

```bash
B=$(aws elbv2 describe-load-balancer-attributes \
  --load-balancer-arn $(aws elbv2 describe-load-balancers --names SIMSPortal --query 'LoadBalancers[0].LoadBalancerArn' --output text) \
  --query "Attributes[?Key=='access_logs.s3.bucket'].Value" --output text)

**CloudFront logs** are files named `cloudfront/E380WF4XO8LWJ7.YYYY-MM-DD-HH.<id>.gz` (the hour is UTC). Lines are tab-separated, after two `#` header lines that name the fields:

```bash
# download a day and search it, e.g. for requests to /scheduler
LOGS=$(mktemp -d)
aws s3 cp s3://$B/cloudfront/ $LOGS --recursive --exclude '*' --include '*.2026-11-24-*'
find $LOGS -name '*.gz' -exec gunzip -c {} + | grep -v '^#' \
  | awk -F'\t' '$8 ~ /^\/scheduler/ {print $1, $2, $5, $6, $8, $9, $11}'   # date time ip method path status user-agent
rm -rf $LOGS
```

Field 1 is the date, 2 the time (UTC), 5 the visitor's IP, 6 the method, 8 the path, 9 the status code, 10 the referrer, 11 the user agent and 12 the query string. The delivery deliberately leaves out the `cs(Cookie)` field, so session cookies are never written to the logs. Keep it that way if you change the fields.

**Load balancer logs** are under `simsportal/AWSLogs/<account ID>/elasticloadbalancing/us-east-2/YYYY/MM/DD/`:

```bash
LOGS=$(mktemp -d)
aws s3 cp s3://$B/simsportal/AWSLogs/ $LOGS --recursive --exclude '*' --include '*/2026/11/24/*'
find $LOGS -name '*.log.gz' -exec gunzip -c {} + | grep '/scheduler'
rm -rf $LOGS
```

Each line is one request, space-separated. Field 2 is the time, field 4 the client (CloudFront) IP and port, field 9 the status code, and fields 13–15 the request line. CloudFront connects over plain HTTP, so it reads `"GET http://rcrcsims.org:80/path HTTP/1.1"`. AWS documents the full format under "Access log entries" for Application Load Balancers.

For searching months at a time, set up Athena on the bucket instead of downloading files.

These logs hold visitors' IP addresses. Keep downloaded copies out of the repo and delete them when you're done.

## Troubleshooting

- **`apt` errors (404) during the build:** the Debian release in the Dockerfile's `FROM` has reached end of life. Move to the next one (that's what #195 did).
- **The site loads with broken images:** `SIMS_Portal/static/assets` must be a symlink to `../../assets/`. The test `test_static_assets_are_served_from_the_assets_folder` guards this.
- **`Can't locate revision …` from `db upgrade`:** the database's migration version isn't in this code's history. Check `flask_task db current`, and don't force it.
- **`aws: Your session has expired`:** run `aws login --profile sims`.
- **The new task keeps restarting:** read its logs (step 7). A common cause is a setting the new code needs that's missing from the task definition.

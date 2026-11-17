-- Production database schema at alembic revision 1f05ced78d0d, before reconciliation
-- (#175 follow-up). SCHEMA ONLY: no rows, no personal data. Generated with
--   pg_restore --schema-only --no-owner --no-privileges <production dump>
-- (psql-only \restrict lines and the PG17+ transaction_timeout setting removed).
-- Used by tests/test_reconcile_production.py to rehearse reconciling production.
--
-- PostgreSQL database dump
--


-- Dumped from database version 14.22
-- Dumped by pg_dump version 18.6

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: public; Type: SCHEMA; Schema: -; Owner: -
--

-- *not* creating schema, since initdb creates it


--
-- Name: update_log_type(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.update_log_type() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
  NEW.log_type = CASE
                  WHEN POSITION('[' IN NEW.message) > 0 AND POSITION(']' IN NEW.message) > POSITION('[' IN NEW.message)
                  THEN SUBSTRING(NEW.message FROM POSITION('[' IN NEW.message) + 1 FOR POSITION(']' IN NEW.message) - POSITION('[' IN NEW.message) - 1)
                  ELSE NULL 
               END;
  RETURN NEW;
END;
$$;


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: acronym; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.acronym (
    id integer NOT NULL,
    acronym_eng character varying(255),
    def_eng character varying(1000),
    expl_eng character varying(1000),
    acronym_esp character varying(255),
    def_esp character varying(1000),
    expl_esp character varying(1000),
    acronym_fra character varying(255),
    def_fra character varying(1000),
    expl_fra character varying(1000),
    relevant_link character varying(1000),
    added_by integer,
    approved_by integer,
    date_added timestamp without time zone,
    date_modified timestamp without time zone,
    anonymous_submitter_name character varying(255),
    anonymous_submitter_email character varying(255),
    scope text,
    field text,
    associated_ns integer
);


--
-- Name: acronym_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.acronym_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: acronym_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.acronym_id_seq OWNED BY public.acronym.id;


--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


--
-- Name: alert; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.alert (
    id integer NOT NULL,
    molnix_id integer,
    alert_record_created_at timestamp without time zone,
    event character varying,
    role_profile character varying,
    rotation character varying,
    modality character varying,
    language_required character varying,
    molnix_status character varying,
    alert_status character varying,
    opens timestamp without time zone,
    start timestamp without time zone,
    end_time timestamp without time zone,
    sectors character varying,
    role_tags character varying,
    scope character varying,
    im_filter boolean,
    iso3 character varying,
    country_name character varying,
    disaster_type_id integer,
    disaster_type_name character varying,
    disaster_go_id integer,
    ifrc_severity_level_display character varying,
    alert_id integer,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone,
    region_id integer
);


--
-- Name: alert_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.alert_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: alert_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.alert_id_seq OWNED BY public.alert.id;


--
-- Name: assignment; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.assignment (
    id integer NOT NULL,
    role character varying(100),
    start_date date,
    end_date date,
    remote boolean,
    assignment_details character varying(1000),
    assignment_status character varying(100),
    availability character varying,
    user_id integer,
    emergency_id integer,
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone,
    hours integer
);


--
-- Name: assignment_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.assignment_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: assignment_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.assignment_id_seq OWNED BY public.assignment.id;


--
-- Name: availability; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.availability (
    id integer NOT NULL,
    dates character varying,
    user_id integer,
    emergency_id integer,
    timeframe character varying,
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone
);


--
-- Name: availability_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.availability_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: availability_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.availability_id_seq OWNED BY public.availability.id;


--
-- Name: badge; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.badge (
    id integer NOT NULL,
    name character varying,
    badge_url character varying,
    description character varying,
    limited_edition boolean
);


--
-- Name: badge_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.badge_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: badge_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.badge_id_seq OWNED BY public.badge.id;


--
-- Name: documentation; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.documentation (
    id integer NOT NULL,
    article_name character varying,
    url character varying,
    category character varying,
    author_id integer NOT NULL,
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone,
    summary character varying,
    portfolio_id integer,
    featured boolean
);


--
-- Name: documentation_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.documentation_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: documentation_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.documentation_id_seq OWNED BY public.documentation.id;


--
-- Name: emergency; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.emergency (
    id integer NOT NULL,
    emergency_name character varying(100) NOT NULL,
    emergency_status character varying(100) NOT NULL,
    emergency_glide character varying(20),
    emergency_go_id integer,
    emergency_location_id integer,
    emergency_review_id integer,
    activation_details character varying(1000),
    slack_channel character varying,
    dropbox_url character varying,
    trello_url character varying,
    emergency_type_id integer,
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone,
    github_repo character varying(255)
);


--
-- Name: emergency_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.emergency_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: emergency_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.emergency_id_seq OWNED BY public.emergency.id;


--
-- Name: emergencytype; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.emergencytype (
    id integer NOT NULL,
    emergency_type_go_id integer,
    emergency_type_name character varying,
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone
);


--
-- Name: emergencytype_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.emergencytype_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: emergencytype_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.emergencytype_id_seq OWNED BY public.emergencytype.id;


--
-- Name: language; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.language (
    id integer NOT NULL,
    name character varying
);


--
-- Name: language_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.language_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: language_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.language_id_seq OWNED BY public.language.id;


--
-- Name: log; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.log (
    id integer NOT NULL,
    message text,
    user_id integer,
    "timestamp" timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    log_type character varying(50)
);


--
-- Name: user; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public."user" (
    id integer NOT NULL,
    firstname character varying(40) NOT NULL,
    lastname character varying(40) NOT NULL,
    status character varying(20),
    birthday date,
    email character varying(120) NOT NULL,
    password character varying(60) NOT NULL,
    molnix_id integer,
    job_title character varying(120),
    unit character varying(120),
    bio text,
    is_admin boolean,
    roles character varying(1000),
    image_file character varying(200) NOT NULL,
    twitter character varying(120),
    slack_id character varying(120),
    github character varying(120),
    linked_in character varying(120),
    messaging_number_country_code integer,
    messaging_number bigint,
    coordinates character varying(120),
    time_zone character varying(120),
    place_label character varying(120),
    ns_id integer,
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone,
    private_profile boolean
);


--
-- Name: latest_logins; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.latest_logins AS
 WITH latestlogins AS (
         SELECT l."timestamp",
            concat(u.firstname, ' ', u.lastname) AS member,
            l.message,
            u.slack_id,
            row_number() OVER (PARTITION BY u.id ORDER BY l."timestamp" DESC) AS rn
           FROM (public.log l
             JOIN public."user" u ON ((u.id = l.user_id)))
          WHERE (l.message ~~ '%logged in%'::text)
        )
 SELECT latestlogins."timestamp",
    latestlogins.member,
    latestlogins.message,
    latestlogins.slack_id
   FROM latestlogins
  WHERE (latestlogins.rn = 1)
  ORDER BY latestlogins."timestamp" DESC;


--
-- Name: learning; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.learning (
    id integer NOT NULL,
    overall_score integer NOT NULL,
    overall_exp character varying NOT NULL,
    got_support integer,
    internal_resource integer,
    external_resource integer,
    field_communication integer,
    clear_tasks integer,
    clear_deadlines integer,
    coordination_tools integer,
    assignment_id integer,
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone
);


--
-- Name: learning_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.learning_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: learning_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.learning_id_seq OWNED BY public.learning.id;


--
-- Name: log_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.log_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: log_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.log_id_seq OWNED BY public.log.id;


--
-- Name: nationalsociety; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.nationalsociety (
    id integer NOT NULL,
    ns_name character varying(120) NOT NULL,
    country_name character varying(120) NOT NULL,
    ns_go_id integer,
    iso2 character varying(2),
    iso3 character varying(3),
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone
);


--
-- Name: nationalsociety_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.nationalsociety_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: nationalsociety_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.nationalsociety_id_seq OWNED BY public.nationalsociety.id;


--
-- Name: no_logins_180_days; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.no_logins_180_days AS
 WITH subquery AS (
         SELECT log_1.user_id,
            max(log_1."timestamp") AS max_timestamp
           FROM public.log log_1
          WHERE (log_1.message ~~ '%logged in%'::text)
          GROUP BY log_1.user_id
        )
 SELECT log.user_id,
    log."timestamp",
    log.message,
    "user".firstname,
    "user".lastname,
    "user".slack_id
   FROM ((public.log log
     JOIN public."user" "user" ON (("user".id = log.user_id)))
     JOIN subquery ON (((log.user_id = subquery.user_id) AND (log."timestamp" = subquery.max_timestamp))))
  WHERE ((log."timestamp" < (CURRENT_TIMESTAMP - '180 days'::interval)) AND (("user".status)::text = 'Active'::text));


--
-- Name: no_logins_194_days; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.no_logins_194_days AS
 WITH subquery AS (
         SELECT log_1.user_id,
            max(log_1."timestamp") AS max_timestamp
           FROM public.log log_1
          WHERE (log_1.message ~~ '%logged in%'::text)
          GROUP BY log_1.user_id
        )
 SELECT log.user_id,
    log."timestamp",
    log.message,
    "user".firstname,
    "user".lastname,
    "user".slack_id
   FROM ((public.log log
     JOIN public."user" "user" ON (("user".id = log.user_id)))
     JOIN subquery ON (((log.user_id = subquery.user_id) AND (log."timestamp" = subquery.max_timestamp))))
  WHERE ((log."timestamp" < (CURRENT_TIMESTAMP - '194 days'::interval)) AND (("user".status)::text = 'Active'::text));


--
-- Name: portfolio; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.portfolio (
    id integer NOT NULL,
    title character varying(200) NOT NULL,
    type character varying(100) NOT NULL,
    format character varying(100),
    description text,
    product_status character varying(100),
    local_file character varying(100) NOT NULL,
    image_file character varying(200),
    dropbox_file character varying(300),
    external boolean,
    collaborator_ids character varying(200),
    approver_id integer,
    approver_message text,
    km_article_id integer,
    assignment_id integer,
    creator_id integer NOT NULL,
    emergency_id integer,
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone,
    learning_site_url character varying(1000)
);


--
-- Name: portfolio_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.portfolio_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: portfolio_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.portfolio_id_seq OWNED BY public.portfolio.id;


--
-- Name: profile; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.profile (
    id integer NOT NULL,
    name character varying,
    image character varying
);


--
-- Name: profile_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.profile_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: profile_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.profile_id_seq OWNED BY public.profile.id;


--
-- Name: region; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.region (
    id integer NOT NULL,
    name character varying(255) NOT NULL
);


--
-- Name: region_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.region_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: region_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.region_id_seq OWNED BY public.region.id;


--
-- Name: regional_focal_point; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.regional_focal_point (
    id integer NOT NULL,
    regional_id integer NOT NULL,
    focal_point_id integer NOT NULL
);


--
-- Name: regional_focal_point_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.regional_focal_point_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: regional_focal_point_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.regional_focal_point_id_seq OWNED BY public.regional_focal_point.id;


--
-- Name: review; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.review (
    id integer NOT NULL,
    category character varying NOT NULL,
    type character varying NOT NULL,
    title character varying NOT NULL,
    description text NOT NULL,
    recommended_action text,
    follow_up text,
    status character varying NOT NULL,
    emergency_id integer NOT NULL,
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone
);


--
-- Name: review_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.review_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: review_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.review_id_seq OWNED BY public.review.id;


--
-- Name: skill; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.skill (
    id integer NOT NULL,
    name character varying,
    category character varying
);


--
-- Name: skill_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.skill_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: skill_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.skill_id_seq OWNED BY public.skill.id;


--
-- Name: story; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.story (
    id integer NOT NULL,
    header_image character varying NOT NULL,
    header_caption character varying NOT NULL,
    entry text,
    emergency_id integer,
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone
);


--
-- Name: story_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.story_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: story_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.story_id_seq OWNED BY public.story.id;


--
-- Name: task; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.task (
    id integer NOT NULL,
    task_id integer,
    repo character varying(100),
    name character varying(500),
    state character varying(10),
    created_by_gh character varying(100),
    url character varying(500),
    assignees_gh character varying(500),
    created_at timestamp without time zone,
    date_added timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    date_modified timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: task_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.task_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: task_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.task_id_seq OWNED BY public.task.id;


--
-- Name: user_badge; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_badge (
    user_id integer,
    badge_id integer,
    assigner_id integer,
    assigner_justify text,
    created_date timestamp without time zone DEFAULT now(),
    updated_date timestamp without time zone
);


--
-- Name: user_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.user_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: user_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.user_id_seq OWNED BY public."user".id;


--
-- Name: user_language; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_language (
    user_id integer,
    language_id integer
);


--
-- Name: user_profile; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_profile (
    user_id integer,
    profile_id integer,
    tier integer
);


--
-- Name: user_skill; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_skill (
    user_id integer,
    skill_id integer
);


--
-- Name: user_workinggroup; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_workinggroup (
    user_id integer,
    workinggroup_id integer
);


--
-- Name: workinggroup; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.workinggroup (
    id integer NOT NULL,
    wg_name character varying NOT NULL,
    wg_description text,
    wg_url character varying,
    wg_external boolean,
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone
);


--
-- Name: workinggroup_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.workinggroup_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: workinggroup_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.workinggroup_id_seq OWNED BY public.workinggroup.id;


--
-- Name: acronym id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.acronym ALTER COLUMN id SET DEFAULT nextval('public.acronym_id_seq'::regclass);


--
-- Name: alert id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alert ALTER COLUMN id SET DEFAULT nextval('public.alert_id_seq'::regclass);


--
-- Name: assignment id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.assignment ALTER COLUMN id SET DEFAULT nextval('public.assignment_id_seq'::regclass);


--
-- Name: availability id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.availability ALTER COLUMN id SET DEFAULT nextval('public.availability_id_seq'::regclass);


--
-- Name: badge id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.badge ALTER COLUMN id SET DEFAULT nextval('public.badge_id_seq'::regclass);


--
-- Name: documentation id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.documentation ALTER COLUMN id SET DEFAULT nextval('public.documentation_id_seq'::regclass);


--
-- Name: emergency id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.emergency ALTER COLUMN id SET DEFAULT nextval('public.emergency_id_seq'::regclass);


--
-- Name: emergencytype id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.emergencytype ALTER COLUMN id SET DEFAULT nextval('public.emergencytype_id_seq'::regclass);


--
-- Name: language id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.language ALTER COLUMN id SET DEFAULT nextval('public.language_id_seq'::regclass);


--
-- Name: learning id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.learning ALTER COLUMN id SET DEFAULT nextval('public.learning_id_seq'::regclass);


--
-- Name: log id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.log ALTER COLUMN id SET DEFAULT nextval('public.log_id_seq'::regclass);


--
-- Name: nationalsociety id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.nationalsociety ALTER COLUMN id SET DEFAULT nextval('public.nationalsociety_id_seq'::regclass);


--
-- Name: portfolio id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.portfolio ALTER COLUMN id SET DEFAULT nextval('public.portfolio_id_seq'::regclass);


--
-- Name: profile id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.profile ALTER COLUMN id SET DEFAULT nextval('public.profile_id_seq'::regclass);


--
-- Name: region id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.region ALTER COLUMN id SET DEFAULT nextval('public.region_id_seq'::regclass);


--
-- Name: regional_focal_point id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.regional_focal_point ALTER COLUMN id SET DEFAULT nextval('public.regional_focal_point_id_seq'::regclass);


--
-- Name: review id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.review ALTER COLUMN id SET DEFAULT nextval('public.review_id_seq'::regclass);


--
-- Name: skill id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.skill ALTER COLUMN id SET DEFAULT nextval('public.skill_id_seq'::regclass);


--
-- Name: story id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.story ALTER COLUMN id SET DEFAULT nextval('public.story_id_seq'::regclass);


--
-- Name: task id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.task ALTER COLUMN id SET DEFAULT nextval('public.task_id_seq'::regclass);


--
-- Name: user id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."user" ALTER COLUMN id SET DEFAULT nextval('public.user_id_seq'::regclass);


--
-- Name: workinggroup id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.workinggroup ALTER COLUMN id SET DEFAULT nextval('public.workinggroup_id_seq'::regclass);


--
-- Name: acronym acronym_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.acronym
    ADD CONSTRAINT acronym_pkey PRIMARY KEY (id);


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: alert alert_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alert
    ADD CONSTRAINT alert_pkey PRIMARY KEY (id);


--
-- Name: assignment assignment_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.assignment
    ADD CONSTRAINT assignment_pkey PRIMARY KEY (id);


--
-- Name: availability availability_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.availability
    ADD CONSTRAINT availability_pkey PRIMARY KEY (id);


--
-- Name: badge badge_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.badge
    ADD CONSTRAINT badge_pkey PRIMARY KEY (id);


--
-- Name: documentation documentation_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.documentation
    ADD CONSTRAINT documentation_pkey PRIMARY KEY (id);


--
-- Name: emergency emergency_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.emergency
    ADD CONSTRAINT emergency_pkey PRIMARY KEY (id);


--
-- Name: emergencytype emergencytype_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.emergencytype
    ADD CONSTRAINT emergencytype_pkey PRIMARY KEY (id);


--
-- Name: language language_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.language
    ADD CONSTRAINT language_pkey PRIMARY KEY (id);


--
-- Name: learning learning_assignment_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.learning
    ADD CONSTRAINT learning_assignment_id_key UNIQUE (assignment_id);


--
-- Name: learning learning_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.learning
    ADD CONSTRAINT learning_pkey PRIMARY KEY (id);


--
-- Name: log log_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.log
    ADD CONSTRAINT log_pkey PRIMARY KEY (id);


--
-- Name: nationalsociety nationalsociety_ns_go_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.nationalsociety
    ADD CONSTRAINT nationalsociety_ns_go_id_key UNIQUE (ns_go_id);


--
-- Name: nationalsociety nationalsociety_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.nationalsociety
    ADD CONSTRAINT nationalsociety_pkey PRIMARY KEY (id);


--
-- Name: portfolio portfolio_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.portfolio
    ADD CONSTRAINT portfolio_pkey PRIMARY KEY (id);


--
-- Name: profile profile_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.profile
    ADD CONSTRAINT profile_pkey PRIMARY KEY (id);


--
-- Name: region region_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.region
    ADD CONSTRAINT region_pkey PRIMARY KEY (id);


--
-- Name: regional_focal_point regional_focal_point_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.regional_focal_point
    ADD CONSTRAINT regional_focal_point_pkey PRIMARY KEY (id);


--
-- Name: review review_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.review
    ADD CONSTRAINT review_pkey PRIMARY KEY (id);


--
-- Name: skill skill_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.skill
    ADD CONSTRAINT skill_pkey PRIMARY KEY (id);


--
-- Name: story story_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.story
    ADD CONSTRAINT story_pkey PRIMARY KEY (id);


--
-- Name: task task_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.task
    ADD CONSTRAINT task_pkey PRIMARY KEY (id);


--
-- Name: user user_email_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."user"
    ADD CONSTRAINT user_email_key UNIQUE (email);


--
-- Name: user user_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."user"
    ADD CONSTRAINT user_pkey PRIMARY KEY (id);


--
-- Name: workinggroup workinggroup_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.workinggroup
    ADD CONSTRAINT workinggroup_pkey PRIMARY KEY (id);


--
-- Name: log before_insert_update_log_type; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER before_insert_update_log_type BEFORE INSERT ON public.log FOR EACH ROW EXECUTE FUNCTION public.update_log_type();


--
-- Name: acronym acronym_added_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.acronym
    ADD CONSTRAINT acronym_added_by_fkey FOREIGN KEY (added_by) REFERENCES public."user"(id);


--
-- Name: acronym acronym_approved_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.acronym
    ADD CONSTRAINT acronym_approved_by_fkey FOREIGN KEY (approved_by) REFERENCES public."user"(id);


--
-- Name: acronym acronym_associated_ns_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.acronym
    ADD CONSTRAINT acronym_associated_ns_fkey FOREIGN KEY (associated_ns) REFERENCES public.nationalsociety(ns_go_id);


--
-- Name: assignment assignment_emergency_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.assignment
    ADD CONSTRAINT assignment_emergency_id_fkey FOREIGN KEY (emergency_id) REFERENCES public.emergency(id);


--
-- Name: assignment assignment_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.assignment
    ADD CONSTRAINT assignment_user_id_fkey FOREIGN KEY (user_id) REFERENCES public."user"(id);


--
-- Name: availability availability_emergency_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.availability
    ADD CONSTRAINT availability_emergency_id_fkey FOREIGN KEY (emergency_id) REFERENCES public.emergency(id);


--
-- Name: availability availability_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.availability
    ADD CONSTRAINT availability_user_id_fkey FOREIGN KEY (user_id) REFERENCES public."user"(id);


--
-- Name: documentation documentation_author_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.documentation
    ADD CONSTRAINT documentation_author_id_fkey FOREIGN KEY (author_id) REFERENCES public."user"(id);


--
-- Name: documentation documentation_portfolio_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.documentation
    ADD CONSTRAINT documentation_portfolio_id_fkey FOREIGN KEY (portfolio_id) REFERENCES public.portfolio(id);


--
-- Name: emergency emergency_emergency_type_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.emergency
    ADD CONSTRAINT emergency_emergency_type_id_fkey FOREIGN KEY (emergency_type_id) REFERENCES public.emergencytype(id);


--
-- Name: learning learning_assignment_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.learning
    ADD CONSTRAINT learning_assignment_id_fkey FOREIGN KEY (assignment_id) REFERENCES public.assignment(id);


--
-- Name: portfolio portfolio_assignment_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.portfolio
    ADD CONSTRAINT portfolio_assignment_id_fkey FOREIGN KEY (assignment_id) REFERENCES public.assignment(id);


--
-- Name: portfolio portfolio_creator_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.portfolio
    ADD CONSTRAINT portfolio_creator_id_fkey FOREIGN KEY (creator_id) REFERENCES public."user"(id);


--
-- Name: portfolio portfolio_emergency_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.portfolio
    ADD CONSTRAINT portfolio_emergency_id_fkey FOREIGN KEY (emergency_id) REFERENCES public.emergency(id);


--
-- Name: regional_focal_point regional_focal_point_focal_point_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.regional_focal_point
    ADD CONSTRAINT regional_focal_point_focal_point_id_fkey FOREIGN KEY (focal_point_id) REFERENCES public."user"(id);


--
-- Name: regional_focal_point regional_focal_point_regional_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.regional_focal_point
    ADD CONSTRAINT regional_focal_point_regional_id_fkey FOREIGN KEY (regional_id) REFERENCES public.region(id);


--
-- Name: review review_emergency_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.review
    ADD CONSTRAINT review_emergency_id_fkey FOREIGN KEY (emergency_id) REFERENCES public.emergency(id);


--
-- Name: story story_emergency_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.story
    ADD CONSTRAINT story_emergency_id_fkey FOREIGN KEY (emergency_id) REFERENCES public.emergency(id);


--
-- Name: user_badge user_badge_badge_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_badge
    ADD CONSTRAINT user_badge_badge_id_fkey FOREIGN KEY (badge_id) REFERENCES public.badge(id);


--
-- Name: user_badge user_badge_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_badge
    ADD CONSTRAINT user_badge_user_id_fkey FOREIGN KEY (user_id) REFERENCES public."user"(id);


--
-- Name: user_language user_language_language_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_language
    ADD CONSTRAINT user_language_language_id_fkey FOREIGN KEY (language_id) REFERENCES public.language(id);


--
-- Name: user_language user_language_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_language
    ADD CONSTRAINT user_language_user_id_fkey FOREIGN KEY (user_id) REFERENCES public."user"(id);


--
-- Name: user user_ns_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."user"
    ADD CONSTRAINT user_ns_id_fkey FOREIGN KEY (ns_id) REFERENCES public.nationalsociety(ns_go_id);


--
-- Name: user_profile user_profile_profile_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_profile
    ADD CONSTRAINT user_profile_profile_id_fkey FOREIGN KEY (profile_id) REFERENCES public.profile(id);


--
-- Name: user_profile user_profile_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_profile
    ADD CONSTRAINT user_profile_user_id_fkey FOREIGN KEY (user_id) REFERENCES public."user"(id);


--
-- Name: user_skill user_skill_skill_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_skill
    ADD CONSTRAINT user_skill_skill_id_fkey FOREIGN KEY (skill_id) REFERENCES public.skill(id);


--
-- Name: user_skill user_skill_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_skill
    ADD CONSTRAINT user_skill_user_id_fkey FOREIGN KEY (user_id) REFERENCES public."user"(id);


--
-- Name: user_workinggroup user_workinggroup_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_workinggroup
    ADD CONSTRAINT user_workinggroup_user_id_fkey FOREIGN KEY (user_id) REFERENCES public."user"(id);


--
-- Name: user_workinggroup user_workinggroup_workinggroup_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_workinggroup
    ADD CONSTRAINT user_workinggroup_workinggroup_id_fkey FOREIGN KEY (workinggroup_id) REFERENCES public.workinggroup(id);


--
-- PostgreSQL database dump complete
--



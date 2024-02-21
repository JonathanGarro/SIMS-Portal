-- automation to parse log level at beginning of message whenever an update runs on the log table

CREATE OR REPLACE FUNCTION public.update_log_type()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
BEGIN
  NEW.log_type = CASE
                  WHEN POSITION('[' IN NEW.message) > 0 AND POSITION(']' IN NEW.message) > POSITION('[' IN NEW.message)
                  THEN SUBSTRING(NEW.message FROM POSITION('[' IN NEW.message) + 1 FOR POSITION(']' IN NEW.message) - POSITION('[' IN NEW.message) - 1)
                  ELSE NULL
               END;
  RETURN NEW;
END;
$function$
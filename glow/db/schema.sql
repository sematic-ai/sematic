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

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: artifacts; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.artifacts (
    id character(40) NOT NULL,
    json_summary jsonb NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    type_serialization jsonb NOT NULL
);


--
-- Name: edges; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.edges (
    id character(32) NOT NULL,
    source_run_id character(32),
    source_name text,
    destination_run_id character(32),
    destination_name text,
    artifact_id character(40),
    parent_id character(32),
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL
);


--
-- Name: runs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.runs (
    id character(32) NOT NULL,
    future_state text NOT NULL,
    name text,
    calculator_path text,
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    started_at timestamp without time zone,
    ended_at timestamp without time zone,
    resolved_at timestamp without time zone,
    failed_at timestamp without time zone,
    parent_id character(32),
    description text,
    tags text,
    source_code text,
    root_id character(32) NOT NULL
);


--
-- Name: schema_migrations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.schema_migrations (
    version character varying(255) NOT NULL
);


--
-- Name: artifacts artifacts_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.artifacts
    ADD CONSTRAINT artifacts_pkey PRIMARY KEY (id);


--
-- Name: edges edges_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.edges
    ADD CONSTRAINT edges_pkey PRIMARY KEY (id);


--
-- Name: runs runs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.runs
    ADD CONSTRAINT runs_pkey PRIMARY KEY (id);


--
-- Name: schema_migrations schema_migrations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.schema_migrations
    ADD CONSTRAINT schema_migrations_pkey PRIMARY KEY (version);


--
-- Name: edges edges_artifact_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.edges
    ADD CONSTRAINT edges_artifact_id_fkey FOREIGN KEY (artifact_id) REFERENCES public.artifacts(id);


--
-- Name: edges edges_destination_run_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.edges
    ADD CONSTRAINT edges_destination_run_id_fkey FOREIGN KEY (destination_run_id) REFERENCES public.runs(id);


--
-- Name: edges edges_parent_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.edges
    ADD CONSTRAINT edges_parent_id_fkey FOREIGN KEY (parent_id) REFERENCES public.edges(id);


--
-- Name: edges edges_source_run_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.edges
    ADD CONSTRAINT edges_source_run_id_fkey FOREIGN KEY (source_run_id) REFERENCES public.runs(id);


--
-- PostgreSQL database dump complete
--


--
-- Dbmate schema migrations
--

INSERT INTO public.schema_migrations (version) VALUES
    ('20220424062956'),
    ('20220514015440'),
    ('20220519154144'),
    ('20220521155045'),
    ('20220521155336'),
    ('20220522082435'),
    ('20220527000512');

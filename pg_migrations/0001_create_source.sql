CREATE TABLE IF NOT EXISTS public.source
(
    id serial NOT NULL,
    iri character varying NOT NULL,
    PRIMARY KEY (id),
    UNIQUE (iri)
)
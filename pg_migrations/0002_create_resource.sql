CREATE TABLE IF NOT  EXISTS public.resource
(
    id serial NOT NULL,
    ori_id bigint NOT NULL,
    iri character varying NOT NULL,
    PRIMARY KEY (id),
    UNIQUE (id),

    CONSTRAINT had_primary_source FOREIGN KEY (iri)
        REFERENCES public.source (iri) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
)
CREATE TABLE documento (
  documento_id SERIAL PRIMARY KEY,
  reintegro_id INTEGER NOT NULL REFERENCES reintegro(reintegro_id),
  tipo VARCHAR(20) NOT NULL CHECK (tipo IN ('FACTURA', 'SOPORTE')),
  filename VARCHAR(255) NOT NULL,
  ruta_local VARCHAR(500) NOT NULL,
  estado VARCHAR(20) DEFAULT 'recibido' CHECK (estado IN ('recibido', 'vinculado', 'reemplazado')),
  checksum VARCHAR(64),
  creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  actualizado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_documento_reintegro_tipo ON documento(reintegro_id, tipo);

-- public.reintegro definition
CREATE TABLE public.reintegro (
	reintegro_id int4 GENERATED ALWAYS AS IDENTITY( INCREMENT BY 1 MINVALUE 1 MAXVALUE 2147483647 START 1 CACHE 1 NO CYCLE) NOT NULL,
	afiliado_id int4 NOT NULL,
	estado text DEFAULT 'pendiente'::text NULL,
	fecha_presentacion timestamp DEFAULT CURRENT_TIMESTAMP NOT NULL,
	total_presentado numeric(12, 2) DEFAULT 0 NULL,
	total_aprobado numeric(12, 2) DEFAULT 0 NULL,
	observaciones text NULL,
	updated_at timestamp DEFAULT now() NOT NULL,
	adjuntos_confirmados bool DEFAULT false NOT NULL,
	CONSTRAINT reintegro_estado_check CHECK ((estado = ANY (ARRAY['pendiente'::text, 'en_revision'::text, 'observado'::text, 'aprobado'::text, 'parcial'::text, 'rechazado'::text, 'liquidado'::text, 'pagado'::text]))),
	CONSTRAINT reintegro_pkey PRIMARY KEY (reintegro_id)
);
CREATE INDEX idx_reintegro_afiliado_fecha ON public.reintegro USING btree (afiliado_id, fecha_presentacion DESC);
CREATE INDEX idx_reintegro_estado ON public.reintegro USING btree (estado, fecha_presentacion);

-- Table Triggers

create trigger tr_reintegro_set_updated_at before
update
    on
    public.reintegro for each row execute function tg_set_updated_at();


-- public.reintegro foreign keys

ALTER TABLE public.reintegro ADD CONSTRAINT reintegro_afiliado_id_fkey FOREIGN KEY (afiliado_id) REFERENCES public.afiliado(afiliado_id);


-- public.reintegro_item definition
CREATE TABLE public.reintegro_item (
	item_id int4 GENERATED ALWAYS AS IDENTITY( INCREMENT BY 1 MINVALUE 1 MAXVALUE 2147483647 START 1 CACHE 1 NO CYCLE) NOT NULL,
	reintegro_id int4 NOT NULL,
	tipo text NOT NULL,
	practica_id int4 NULL,
	medicamento_id int4 NULL,
	fecha_prestacion date NOT NULL,
	monto_presentado numeric(12, 2) NOT NULL,
	monto_aprobado numeric(12, 2) NULL,
	cobertura_aplicada numeric(5, 2) NULL,
	copago numeric(12, 2) NULL,
	prestador_txt text NULL,
	comprobante_txt text NULL,
	CONSTRAINT reintegro_item_pkey PRIMARY KEY (item_id),
	CONSTRAINT reintegro_item_tipo_check CHECK ((tipo = ANY (ARRAY['practica'::text, 'medicamento'::text])))
);
CREATE INDEX idx_reintegro_item_reintegro_fecha ON public.reintegro_item USING btree (reintegro_id, fecha_prestacion);


-- public.reintegro_item foreign keys

ALTER TABLE public.reintegro_item ADD CONSTRAINT reintegro_item_medicamento_id_fkey FOREIGN KEY (medicamento_id) REFERENCES public.medicamento(medicamento_id);
ALTER TABLE public.reintegro_item ADD CONSTRAINT reintegro_item_practica_id_fkey FOREIGN KEY (practica_id) REFERENCES public.practica(practica_id);
ALTER TABLE public.reintegro_item ADD CONSTRAINT reintegro_item_reintegro_id_fkey FOREIGN KEY (reintegro_id) REFERENCES public.reintegro(reintegro_id) ON DELETE CASCADE;

-- public.afiliado definition
CREATE TABLE public.afiliado (
	afiliado_id int4 GENERATED ALWAYS AS IDENTITY( INCREMENT BY 1 MINVALUE 1 MAXVALUE 2147483647 START 1 CACHE 1 NO CYCLE) NOT NULL,
	tipo_doc text NOT NULL,
	nro_doc text NOT NULL,
	nombre text NOT NULL,
	apellido text NOT NULL,
	fecha_nac date NULL,
	email text NULL,
	tel text NULL,
	plan_id int4 NULL,
	CONSTRAINT afiliado_pkey PRIMARY KEY (afiliado_id),
	CONSTRAINT afiliado_tipo_doc_nro_doc_key UNIQUE (tipo_doc, nro_doc)
);
CREATE INDEX idx_afiliado_doc ON public.afiliado USING btree (tipo_doc, nro_doc);

-- public.afiliado foreign keys

ALTER TABLE public.afiliado ADD CONSTRAINT afiliado_plan_id_fkey FOREIGN KEY (plan_id) REFERENCES public."plan"(plan_id);


-- public.reintegro definition
CREATE TABLE public.reintegro (
	reintegro_id int4 GENERATED ALWAYS AS IDENTITY( INCREMENT BY 1 MINVALUE 1 MAXVALUE 2147483647 START 1 CACHE 1 NO CYCLE) NOT NULL,
	afiliado_id int4 NOT NULL,
	estado text DEFAULT 'PENDIENTE'::text NOT NULL,
	fecha_presentacion timestamp DEFAULT CURRENT_TIMESTAMP NOT NULL,
	total_presentado numeric(12, 2) DEFAULT 0 NULL,
	total_aprobado numeric(12, 2) DEFAULT 0 NULL,
	observaciones text NULL,
	cbu varchar(22) NOT NULL,
	adjuntos_confirmados bool DEFAULT false NOT NULL,
	CONSTRAINT reintegro_pkey PRIMARY KEY (reintegro_id),
	CONSTRAINT reintegro_afiliado_id_fkey FOREIGN KEY (afiliado_id) REFERENCES public.afiliado(afiliado_id)
);
CREATE INDEX idx_reintegro_afiliado ON public.reintegro USING btree (afiliado_id);
CREATE INDEX idx_reintegro_estado_fecha ON public.reintegro USING btree (estado, fecha_presentacion);

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
	numero_afiliado bpchar(8) DEFAULT '00000000'::bpchar NOT NULL,
	domicilio text NULL,
	CONSTRAINT afiliado_pkey PRIMARY KEY (afiliado_id),
	CONSTRAINT afiliado_tipo_doc_nro_doc_key UNIQUE (tipo_doc, nro_doc),
	CONSTRAINT afiliado_plan_id_fkey FOREIGN KEY (plan_id) REFERENCES public."plan"(plan_id)
);
CREATE INDEX idx_afiliado_doc ON public.afiliado USING btree (tipo_doc, nro_doc);

CREATE TABLE public.documentos_reintegro (
	documento_id int4 GENERATED ALWAYS AS IDENTITY( INCREMENT BY 1 MINVALUE 1 MAXVALUE 2147483647 START 1 CACHE 1 NO CYCLE) NOT NULL,
	reintegro_id int4 NOT NULL,
	tipo text NOT NULL,
	filename text NOT NULL,
	ruta_local text NOT NULL,
	estado text DEFAULT 'recibido'::text NOT NULL,
	checksum text NULL,
	creado_en timestamp DEFAULT now() NOT NULL,
	actualizado_en timestamp DEFAULT now() NOT NULL,
	CONSTRAINT documento_estado_check CHECK ((estado = ANY (ARRAY['recibido'::text, 'vinculado'::text, 'reemplazado'::text]))),
	CONSTRAINT documento_pkey PRIMARY KEY (documento_id)
);
CREATE INDEX idx_documento_reintegro_tipo ON public.documentos_reintegro USING btree (reintegro_id, tipo);

CREATE TABLE afiliacion (
    id SERIAL PRIMARY KEY,
    nombre_apellido VARCHAR(150) NOT NULL,
    dni BIGINT UNIQUE NOT NULL CHECK (dni > 0),
    fecha_nacimiento DATE NOT NULL CHECK (
        -- Debe tener al menos 18 años
        AGE(CURRENT_DATE, fecha_nacimiento) >= INTERVAL '18 years'
    ),
    domicilio_calle VARCHAR(100) NOT NULL,
    domicilio_numero VARCHAR(10) NOT NULL,
    localidad VARCHAR(100) NOT NULL,
    provincia VARCHAR(100) NOT NULL,
    telefono VARCHAR(30),
    email VARCHAR(150),
    tipo_afiliado VARCHAR(20) NOT NULL CHECK (
        tipo_afiliado IN ('EMPLEADO', 'MONOTRIBUTISTA', 'JUBILADO', 'PARTICULAR')
    ),
    estado text DEFAULT 'PENDIENTE'::text NOT NULL,
    adjuntos_confirmados bool DEFAULT false NOT NULL
)

-- =========================================
-- Tabla: public.documentos_afiliacion
-- =========================================
CREATE TABLE public.documentos_afiliacion (
    documento_id int4 GENERATED ALWAYS AS IDENTITY (
        INCREMENT BY 1 MINVALUE 1 MAXVALUE 2147483647 START 1 CACHE 1 NO CYCLE
    ) NOT NULL,
    afiliacion_id int4 NOT NULL,
    tipo text NOT NULL,
    filename text NOT NULL,
    ruta_local text NOT NULL,
    estado text DEFAULT 'recibido'::text NOT NULL,
    checksum text NULL,
    creado_en timestamp DEFAULT now() NOT NULL,
    actualizado_en timestamp DEFAULT now() NOT NULL,
    CONSTRAINT documento_afiliacion_pkey PRIMARY KEY (documento_id),
    CONSTRAINT documento_afiliacion_estado_check CHECK (
        estado = ANY (ARRAY['recibido'::text, 'vinculado'::text, 'reemplazado'::text])
    ),
    CONSTRAINT documento_afiliacion_fk
        FOREIGN KEY (afiliacion_id) REFERENCES public.afiliacion(id)
        ON UPDATE CASCADE
        ON DELETE CASCADE
);

-- Índice para búsquedas por afiliación y tipo
CREATE INDEX idx_documento_afiliacion_tipo
    ON public.documentos_afiliacion USING btree (afiliacion_id, tipo);

-- Trigger para mantener actualizado 'actualizado_en'
CREATE TRIGGER tr_documento_afiliacion_set_actualizado_en
BEFORE UPDATE ON public.documentos_afiliacion
FOR EACH ROW
EXECUTE FUNCTION tg_set_actualizado_en();

-- public.practica definition
CREATE TABLE public.practica (
	practica_id int4 GENERATED ALWAYS AS IDENTITY( INCREMENT BY 1 MINVALUE 1 MAXVALUE 2147483647 START 1 CACHE 1 NO CYCLE) NOT NULL,
	codigo text NOT NULL,
	nombre text NOT NULL,
	requiere_autorizacion int4 DEFAULT 0 NULL,
	CONSTRAINT practica_codigo_key UNIQUE (codigo),
	CONSTRAINT practica_pkey PRIMARY KEY (practica_id)
);

-- public.medicamento definition
CREATE TABLE public.medicamento (
	medicamento_id int4 GENERATED ALWAYS AS IDENTITY( INCREMENT BY 1 MINVALUE 1 MAXVALUE 2147483647 START 1 CACHE 1 NO CYCLE) NOT NULL,
	principio_activo text NOT NULL,
	marca text NULL,
	CONSTRAINT medicamento_pkey PRIMARY KEY (medicamento_id)
);
-- ==============================================================================
-- Semilla de Tiendas y Editoriales Oficiales de Bolivia (14 Fuentes)
-- ==============================================================================

INSERT INTO stores (name, slug, city, website_url, cms_type, is_publisher_store, default_publisher_name)
VALUES
    ('Librerías Lectura', 'librerias-lectura', 'La Paz / Santa Cruz', 'https://libreriaslectura.com/', 'woocommerce', false, NULL),
    ('SBS Librería Internacional', 'sbs-libreria', 'La Paz / Cochabamba / Santa Cruz', 'https://www.sbs.com.bo/', 'wix', false, NULL),
    ('Librería Kronos', 'libreria-kronos', 'La Paz', 'https://libreriakronos.com/', 'shopify', false, NULL),
    ('El Baúl del Libro', 'el-baul-del-libro', 'Envíos Nacionales', 'https://bauldellibro.com/', 'woocommerce', false, NULL),
    ('Grupo Editorial Kipus', 'editorial-kipus', 'Cochabamba', 'https://editorialkipus.com/', 'woocommerce', true, 'Editorial Kipus'),
    ('Editorial El Cuervo', 'editorial-el-cuervo', 'La Paz', 'https://www.editorialelcuervo.com/', 'woocommerce', true, 'Editorial El Cuervo'),
    ('Plural Editores', 'plural-editores', 'La Paz', 'https://plural-editores.com/', 'woocommerce', true, 'Plural Editores'),
    ('Grupo Editorial La Hoguera', 'la-hoguera', 'Santa Cruz', 'https://www.lahoguera.com/', 'custom', true, 'Editorial La Hoguera'),
    ('Encantalibros', 'encantalibros', 'La Paz / Envíos Nacionales', 'https://encantalibros.com/', 'woocommerce', false, NULL),
    ('Libroclik', 'libroclik', 'Envíos Nacionales', 'https://libroclik.com/', 'custom', false, NULL),
    ('Vínculos', 'vinculos', 'La Paz', 'https://vinculos.com.bo/', 'woocommerce', false, NULL),
    ('El Bagallero Ilustrado', 'el-bagallero-ilustrado', 'Tarija / Envíos Nacionales', 'https://bagalleroilustrado.com/', 'shopify', false, NULL),
    ('Librería D&C', 'libreria-dc', 'Envíos Nacionales', 'https://libreriadc.com.bo/', 'woocommerce', false, NULL),
    ('Librerías Don Bosco', 'librerias-don-bosco', 'La Paz / Sucre', 'https://www.libreriasdonbosco.com/', 'woocommerce', false, NULL),
    ('Librería Yachaywasi', 'libreria-yachaywasi', 'La Paz / Cochabamba', 'https://libreriayachaywasi.com/', 'shopify', false, NULL)
ON CONFLICT (slug) DO UPDATE 
SET 
    website_url = EXCLUDED.website_url,
    cms_type = EXCLUDED.cms_type,
    is_publisher_store = EXCLUDED.is_publisher_store,
    default_publisher_name = EXCLUDED.default_publisher_name;

-- Pre-cargar editoriales bolivianas de renombre
INSERT INTO publishers (name, slug, country)
VALUES
    ('Plural Editores', 'plural-editores', 'Bolivia'),
    ('Editorial Kipus', 'editorial-kipus', 'Bolivia'),
    ('Editorial El Cuervo', 'editorial-el-cuervo', 'Bolivia'),
    ('Editorial La Hoguera', 'editorial-la-hoguera', 'Bolivia'),
    ('Editorial 3600', 'editorial-3600', 'Bolivia'),
    ('Nuevo Milenio', 'nuevo-milenio', 'Bolivia'),
    ('Gisbert', 'gisbert', 'Bolivia'),
    ('Alfaguara', 'alfaguara', 'Internacional'),
    ('Anagrama', 'anagrama', 'Internacional'),
    ('Alianza Editorial', 'alianza-editorial', 'Internacional'),
    ('Penguin Random House', 'penguin-random-house', 'Internacional'),
    ('Planeta', 'planeta', 'Internacional'),
    ('Cátedra', 'catedra', 'Internacional'),
    ('Debolsillo', 'debolsillo', 'Internacional'),
    ('Fondo de Cultura Económica', 'fce', 'Internacional')
ON CONFLICT (name) DO NOTHING;

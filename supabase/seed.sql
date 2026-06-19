-- ──────────────────────────────────────────────────────────────────
-- seed.sql — Agrolytics Phase 1 Dummy Data
-- ──────────────────────────────────────────────────────────────────
-- Reproducible seed: 56 regions Kalimantan + realistic dummy timeseries.
-- Idempotent — safe to re-run (truncates data tables first, NOT profiles
-- or audit_log which depend on auth.users / admin actions).
--
-- Run: psql "<connection-string>" -f supabase/seed.sql
--   or: supabase db reset   (auto-applies migrations then this seed)
--
-- Production numbers are SYNTHETIC (hashtext-based deterministic noise),
-- to be replaced by real BPS/NASA POWER + LSTM output in Phase 2.
-- ──────────────────────────────────────────────────────────────────

truncate table public.cluster_assignments,
               public.predictions,
               public.weather_history,
               public.production_history,
               public.regions
  restart identity cascade;

-- ── Regions: 56 kabupaten/kota across 5 provinces ──────────────────
insert into public.regions (bps_code, name, province, province_code, centroid_lat, centroid_lng, geojson_id) values
-- Kalimantan Barat (14)
('6101','Kabupaten Sambas','Kalimantan Barat','61',1.36,109.30,'6101'),
('6102','Kabupaten Bengkayang','Kalimantan Barat','61',1.05,109.66,'6102'),
('6103','Kabupaten Landak','Kalimantan Barat','61',0.46,109.97,'6103'),
('6104','Kabupaten Mempawah','Kalimantan Barat','61',0.32,108.93,'6104'),
('6105','Kabupaten Sanggau','Kalimantan Barat','61',0.13,110.59,'6105'),
('6106','Kabupaten Ketapang','Kalimantan Barat','61',-1.85,110.18,'6106'),
('6107','Kabupaten Sintang','Kalimantan Barat','61',0.07,111.50,'6107'),
('6108','Kabupaten Kapuas Hulu','Kalimantan Barat','61',0.85,112.93,'6108'),
('6109','Kabupaten Sekadau','Kalimantan Barat','61',0.03,110.96,'6109'),
('6110','Kabupaten Melawi','Kalimantan Barat','61',-0.34,111.69,'6110'),
('6111','Kabupaten Kayong Utara','Kalimantan Barat','61',-1.04,109.95,'6111'),
('6112','Kabupaten Kubu Raya','Kalimantan Barat','61',-0.16,109.36,'6112'),
('6171','Kota Pontianak','Kalimantan Barat','61',-0.026,109.34,'6171'),
('6172','Kota Singkawang','Kalimantan Barat','61',0.91,108.98,'6172'),
-- Kalimantan Tengah (14)
('6201','Kabupaten Kotawaringin Barat','Kalimantan Tengah','62',-2.50,111.62,'6201'),
('6202','Kabupaten Kotawaringin Timur','Kalimantan Tengah','62',-2.04,112.62,'6202'),
('6203','Kabupaten Kapuas','Kalimantan Tengah','62',-2.00,114.10,'6203'),
('6204','Kabupaten Barito Selatan','Kalimantan Tengah','62',-1.86,114.78,'6204'),
('6205','Kabupaten Barito Utara','Kalimantan Tengah','62',-0.97,114.93,'6205'),
('6206','Kabupaten Sukamara','Kalimantan Tengah','62',-2.62,111.24,'6206'),
('6207','Kabupaten Lamandau','Kalimantan Tengah','62',-1.51,111.21,'6207'),
('6208','Kabupaten Seruyan','Kalimantan Tengah','62',-2.50,112.18,'6208'),
('6209','Kabupaten Katingan','Kalimantan Tengah','62',-1.55,113.05,'6209'),
('6210','Kabupaten Pulang Pisau','Kalimantan Tengah','62',-2.81,114.07,'6210'),
('6211','Kabupaten Gunung Mas','Kalimantan Tengah','62',-1.10,113.50,'6211'),
('6212','Kabupaten Barito Timur','Kalimantan Tengah','62',-2.05,115.00,'6212'),
('6213','Kabupaten Murung Raya','Kalimantan Tengah','62',-0.10,114.00,'6213'),
('6271','Kota Palangka Raya','Kalimantan Tengah','62',-2.21,113.92,'6271'),
-- Kalimantan Selatan (13)
('6301','Kabupaten Tanah Laut','Kalimantan Selatan','63',-3.85,114.78,'6301'),
('6302','Kabupaten Kotabaru','Kalimantan Selatan','63',-2.78,116.20,'6302'),
('6303','Kabupaten Banjar','Kalimantan Selatan','63',-3.32,114.92,'6303'),
('6304','Kabupaten Barito Kuala','Kalimantan Selatan','63',-3.05,114.69,'6304'),
('6305','Kabupaten Tapin','Kalimantan Selatan','63',-3.00,115.04,'6305'),
('6306','Kabupaten Hulu Sungai Selatan','Kalimantan Selatan','63',-2.66,115.27,'6306'),
('6307','Kabupaten Hulu Sungai Tengah','Kalimantan Selatan','63',-2.61,115.41,'6307'),
('6308','Kabupaten Hulu Sungai Utara','Kalimantan Selatan','63',-2.42,115.25,'6308'),
('6309','Kabupaten Tabalong','Kalimantan Selatan','63',-1.83,115.55,'6309'),
('6310','Kabupaten Tanah Bumbu','Kalimantan Selatan','63',-3.45,115.83,'6310'),
('6311','Kabupaten Balangan','Kalimantan Selatan','63',-2.32,115.69,'6311'),
('6371','Kota Banjarmasin','Kalimantan Selatan','63',-3.32,114.59,'6371'),
('6372','Kota Banjarbaru','Kalimantan Selatan','63',-3.45,114.83,'6372'),
-- Kalimantan Timur (10)
('6401','Kabupaten Paser','Kalimantan Timur','64',-1.84,116.20,'6401'),
('6402','Kabupaten Kutai Barat','Kalimantan Timur','64',-0.30,115.60,'6402'),
('6403','Kabupaten Kutai Kartanegara','Kalimantan Timur','64',-0.43,116.95,'6403'),
('6404','Kabupaten Kutai Timur','Kalimantan Timur','64',1.03,117.78,'6404'),
('6405','Kabupaten Berau','Kalimantan Timur','64',2.15,117.49,'6405'),
('6409','Kabupaten Penajam Paser Utara','Kalimantan Timur','64',-1.27,116.83,'6409'),
('6411','Kabupaten Mahakam Ulu','Kalimantan Timur','64',0.65,114.86,'6411'),
('6471','Kota Balikpapan','Kalimantan Timur','64',-1.27,116.83,'6471'),
('6472','Kota Samarinda','Kalimantan Timur','64',-0.50,117.15,'6472'),
('6474','Kota Bontang','Kalimantan Timur','64',0.13,117.50,'6474'),
-- Kalimantan Utara (5)
('6501','Kabupaten Malinau','Kalimantan Utara','65',3.59,116.65,'6501'),
('6502','Kabupaten Bulungan','Kalimantan Utara','65',2.85,117.40,'6502'),
('6503','Kabupaten Tana Tidung','Kalimantan Utara','65',3.55,117.13,'6503'),
('6504','Kabupaten Nunukan','Kalimantan Utara','65',4.13,116.74,'6504'),
('6571','Kota Tarakan','Kalimantan Utara','65',3.30,117.63,'6571');

-- ── production_history: 56 × 8 tahun (2018–2025) = 448 rows ─────────
insert into public.production_history (region_id, year, month, production_ton, area_harvest_ha, yield_ton_ha, source)
select
  r.id, y.year, null,
  round((p.base_yield * p.area * (1 + 0.05 * sin((y.year - 2018)::numeric)) * (1 + (hashtext(r.id::text || y.year::text)::float / 2147483647 * 0.15)))::numeric, 2),
  round((p.area * (1 + 0.02 * (y.year - 2018)))::numeric, 2),
  round((p.base_yield * (1 + 0.03 * (y.year - 2018)) * (1 + (hashtext(r.id::text || y.year::text)::float / 2147483647 * 0.10)))::numeric, 3),
  'BPS'
from public.regions r
cross join generate_series(2018, 2025) as y(year)
cross join lateral (
  select
    case r.province
      when 'Kalimantan Selatan' then 4.6
      when 'Kalimantan Tengah' then 3.8
      when 'Kalimantan Barat' then 3.5
      when 'Kalimantan Timur' then 3.2
      when 'Kalimantan Utara' then 2.9
    end as base_yield,
    case when r.name like 'Kota%' then 1500 else 12000 + (hashtext(r.id::text)::int % 8000) end as area
) p;

-- ── weather_history: 56 × 8 tahun × 12 bulan = 5,376 rows ───────────
insert into public.weather_history (region_id, year, month, rainfall_mm, temp_avg_c, temp_min_c, temp_max_c, humidity_pct, solar_radiation, source)
select
  r.id, y.year, m.month,
  round((180 + 100 * sin(m.month::numeric * 0.5) + (hashtext(r.id::text || y.year::text || m.month::text)::float / 2147483647 * 80))::numeric, 1),
  round((26.5 + 1.2 * cos((m.month - 7)::numeric * 0.5) + (hashtext(r.id::text || y.year::text || m.month::text)::float / 2147483647 * 1.5))::numeric, 1),
  round((22.5 + cos((m.month - 7)::numeric * 0.5) + (hashtext(r.id::text || m.month::text)::float / 2147483647 * 1.0))::numeric, 1),
  round((31.5 + 1.5 * cos((m.month - 7)::numeric * 0.5) + (hashtext(r.id::text || m.month::text)::float / 2147483647 * 1.2))::numeric, 1),
  round((82 + 5 * sin(m.month::numeric * 0.5) + (hashtext(r.id::text || y.year::text)::float / 2147483647 * 4))::numeric, 1),
  round((18 + 3 * cos((m.month - 3)::numeric * 0.5) + (hashtext(r.id::text)::float / 2147483647 * 2))::numeric, 2),
  'NASA_POWER'
from public.regions r
cross join generate_series(2018, 2025) as y(year)
cross join generate_series(1, 12) as m(month);

-- ── predictions: 56 × 4 model × target 2026 = 224 rows ──────────────
insert into public.predictions (region_id, target_year, target_month, predicted_yield, predicted_prod_ton, confidence_lower, confidence_upper, model_name, model_version, is_baseline)
select
  r.id, 2026, null,
  round((p.base_yield * (1 + 0.03 * 8) * m.bias)::numeric, 3),
  round((p.base_yield * p.area * (1 + 0.05 * sin(8::numeric)) * m.bias)::numeric, 2),
  round((p.base_yield * (1 + 0.03 * 8) * m.bias * 0.92)::numeric, 3),
  round((p.base_yield * (1 + 0.03 * 8) * m.bias * 1.08)::numeric, 3),
  m.name, 'v1-dummy',
  (m.name = 'lstm')
from public.regions r
cross join lateral (
  select
    case r.province
      when 'Kalimantan Selatan' then 4.6
      when 'Kalimantan Tengah' then 3.8
      when 'Kalimantan Barat' then 3.5
      when 'Kalimantan Timur' then 3.2
      when 'Kalimantan Utara' then 2.9
    end as base_yield,
    case when r.name like 'Kota%' then 1500 else 12000 + (hashtext(r.id::text)::int % 8000) end as area
) p
cross join (values ('lstm', 1.05), ('xgboost', 1.02), ('random_forest', 0.98), ('linear', 0.95)) as m(name, bias);

-- ── cluster_assignments: 56 rows, K-means dummy (ntile on yield) ────
insert into public.cluster_assignments (region_id, cluster_label, cluster_name, reference_year)
select
  region_id,
  case when ntile_rank = 1 then 0 when ntile_rank = 2 then 1 else 2 end,
  case when ntile_rank = 1 then 'Prioritas Tinggi' when ntile_rank = 2 then 'Prioritas Sedang' else 'Prioritas Rendah' end,
  2025
from (
  select p.region_id, ntile(3) over (order by p.predicted_yield desc) as ntile_rank
  from public.predictions p
  where p.model_name = 'lstm' and p.target_year = 2026
) ranked;

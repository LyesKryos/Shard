--
-- PostgreSQL database dump
--

-- Dumped from database version 12.18 (Ubuntu 12.18-0ubuntu0.20.04.1)
-- Dumped by pg_dump version 12.18 (Ubuntu 12.18-0ubuntu0.20.04.1)

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
-- Name: cnc_provinces; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.cnc_provinces (
    id integer,
    terrain integer,
    bordering integer[],
    owner text DEFAULT ''::text,
    owner_id bigint DEFAULT 0,
    troops integer DEFAULT 0,
    coast boolean,
    cord point,
    river boolean DEFAULT false,
    value text,
    port boolean DEFAULT false,
    fort boolean DEFAULT false,
    city boolean DEFAULT false,
    manpower bigint DEFAULT 0,
    name text,
    unrest integer DEFAULT 0,
    event integer DEFAULT 0,
    uprising boolean DEFAULT false,
    occupier text DEFAULT ''::text,
    occupier_id bigint DEFAULT 0,
    workshop boolean DEFAULT false,
    temple boolean DEFAULT false,
    production integer
);


ALTER TABLE public.cnc_provinces OWNER TO postgres;

--
-- Data for Name: cnc_provinces; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.cnc_provinces (id, terrain, bordering, owner, owner_id, troops, coast, cord, river, value, port, fort, city, manpower, name, unrest, event, uprising, occupier, occupier_id, workshop, temple, production) FROM stdin;
934	0	{931,933,935,936,937,938,939}	Khokand	905858887926816768	377	f	(2677,1384)	t	Ivory	f	f	f	3018	Seva	14	0	f	Khokand	905858887926816768	f	f	2
992	0	{991,993,994,995,996,997}	New Crea	692089085690380288	1298	t	(3782,1249)	f	Paper	f	f	f	3290	Cupo	5	0	f	New Crea	692089085690380288	f	f	1
786	2	{785,787}	Correlli	293518673417732098	0	t	(3176,27)	f	Salt	f	f	f	3871	Kenupis	0	0	f	Correlli	293518673417732098	f	f	1
1129	0	{1128,1130,1131,1143}	Khokand	905858887926816768	0	t	(2837,1796)	f	Glass	f	f	f	3317	Behbu	18	0	f	Khokand	905858887926816768	f	f	3
753	2	{747,748,749,752,754,758,759}	Correlli	293518673417732098	0	f	(3251,211)	f	Glass	f	f	f	2738	Athyastoroklis	0	0	f	Correlli	293518673417732098	f	f	1
776	2	{775,777,779}	Correlli	293518673417732098	0	t	(3035,132)	f	Wood	f	f	f	4419	Eubacus	0	0	f	Correlli	293518673417732098	f	f	1
797	9	{796,798,799}	Nokoroth	428949783919460363	0	t	(3660,48)	f	Ivory	f	f	f	269	Acne	0	0	f	Nokoroth	428949783919460363	f	f	1
1213	0	{0}	Nokoroth	428949783919460363	0	t	(3436,2288)	f	Wool	f	f	f	3122	Thayatseng	0	0	f	Nokoroth	428949783919460363	f	f	3
771	0	{0}		0	2528	t	(3369,496)	f	Fur	f	f	f	4891	Landtals	0	0	f		0	f	f	1
811	2	{802,810,812,813,814}	Correlli	293518673417732098	0	t	(3312,106)	f	Salt	f	f	f	2760	Shari	0	0	f	Correlli	293518673417732098	f	f	2
104	2	{99,100,102,103,110}	Nanhai	899852149360566323	0	t	(592,722)	f	Livestock	f	f	f	2654	Tyraphos	0	0	f	Nanhai	899852149360566323	f	f	2
1009	0	{1002,1008,1010,1035,1044,1045}	New Crea	692089085690380288	102	f	(3573,1519)	t	Paper	f	f	f	3320	Sepdjesut	16	0	f	New Crea	692089085690380288	f	f	1
360	0	{361,362,387,443}	Litchmiota	637939981691912202	0	t	(1440,1269)	f	Spices	f	f	f	3852	Rhegenes	15	0	f	Litchmiota	637939981691912202	f	f	3
598	0	{533,534,535,597,599}	Tusail	844640695868194927	0	f	(1026,2259)	t	Glass	f	f	f	3503	Gesso	23	0	f	Tusail	844640695868194927	f	f	2
1056	2	{1053,1055,1057}	Nokoroth	428949783919460363	0	t	(3613,2167)	f	Tea and Coffee	f	f	f	3201	Nuotebiki	0	0	f	Nokoroth	428949783919460363	f	f	2
1166	5	{1162,1165,1167}	Blindgulf	967635049061163028	0	f	(2903,2410)	f	Tin	f	f	f	720	Joggrox	0	0	f	Blindgulf	967635049061163028	f	f	4
4	0	{2,3,5,6,7}		0	316	t	(859,1354)	f	Spices	f	f	f	4689	Kezubenu	0	0	f		0	f	f	3
196	9	{192,193,197,197}	Ghad	281967961189908482	650	t	(1210,250)	f	Fish	t	f	f	209	Bema	0	0	f	Ghad	281967961189908482	f	f	3
929	0	{928,930}	Khokand	905858887926816768	0	t	(2871,1253)	f	Wood	f	f	f	3256	Djacahdet	18	0	f	Khokand	905858887926816768	f	f	1
347	5	{331,345,346}		0	1178	f	(1910,475)	f	Iron	f	f	f	713	Tarnouru	0	0	f		0	f	f	4
872	2	{870,871,873,878,879,880}	Blindgulf	0	3850	f	(3958,256)	f	Wood	f	f	f	2855	Aurigneux	0	0	f		0	f	f	2
903	0	{893,894,895,902,904}	Blindgulf	0	6110	f	(3901,544)	t	Tobacco	f	f	f	3055	Menrusiris	0	0	f		0	f	f	1
858	9	{855,857,859}	Blindgulf	0	484	t	(3679,117)	f	Spices	f	f	f	242	Napby	0	0	f		0	f	f	3
960	0	{944,959,961,1094,1095,1096,1097}		0	309	f	(3042,1519)	t	Wood	f	f	f	4450	Shapo	0	0	f		0	f	f	1
310	0	{305,306,309,311,312,429}		0	306	f	(1681,625)	f	Paper	f	f	f	4774	Senebenu	0	0	f		0	f	f	1
644	2	{643,645,648}		0	330	t	(2675,342)	f	Wine	f	f	f	4390	Tabe	0	0	f		0	f	f	3
6	0	{4,5,7,8,9}		0	335	t	(916,1318)	f	Livestock	f	f	f	3020	Dessasiris	0	0	f		0	f	f	3
313	2	{312,314,332,431}		0	337	f	(1721,475)	f	Grain	f	f	f	3598	Tarre	0	0	f		0	f	f	1
710	2	{702,703,709,711,712}		0	384	f	(2720,855)	t	Iron	f	f	f	4352	Nemtadjed	0	0	f		0	f	f	4
830	5	{823,829,831}		0	1132	t	(3431,119)	f	Raw Stone	f	f	f	732	Behzum	0	0	f		0	f	f	2
994	0	{992,993,995}		0	331	t	(3820,1204)	f	Paper	f	f	f	4996	Wasbumunein	0	0	f		0	f	f	2
75	2	{74,76,79,80,94,98}		0	313	f	(508,893)	t	Tea and Coffee	f	f	f	2788	Khemabesheh	0	0	f		0	f	f	2
91	2	{87,90,92}		0	300	t	(337,889)	f	Iron	f	f	f	3748	Epione	0	0	f		0	f	f	1
171	5	{169,170,474}		0	1207	f	(1449,686)	f	Tin	f	f	f	815	Pelyma	0	0	f		0	f	f	2
267	0	{144,253,256,268,289}		0	284	f	(1087,936)	f	Glass	f	f	f	3485	Golgona	0	0	f		0	f	f	3
304	0	{302,303,306,306,314}		0	379	f	(1645,520)	f	Fur	f	f	f	3909	Thebekion	0	0	f		0	f	f	2
10	0	{3,5,9,11,12,28}		0	346	f	(790,1273)	t	Sugar	f	f	f	4654	Phanipolis	0	0	f		0	f	f	2
263	5	{294,415}		0	1276	f	(1395,909)	f	Salt	f	f	f	794	Rhodyrgos	0	0	f		0	f	f	3
89	5	{88,90}		0	1011	t	(369,817)	f	Salt	f	f	f	783	Myrolgi	0	0	f		0	f	f	3
498	1	{496,505,506}		0	116	t	(1188,1260)	f	Paper	f	f	f	696	Laodigona	0	0	f		0	f	f	2
214	2	{212,216}	Ghad	281967961189908482	650	t	(1062,463)	f	Fur	t	f	f	2704	Golgarae	0	0	f	Ghad	281967961189908482	t	f	1
146	0	{145,147,297}	Litchmiota	637939981691912202	0	t	(1204,1008)	t	Wood	t	f	f	3044	Corcyreum	15	0	f	Litchmiota	637939981691912202	t	f	4
276	7	{241,242,251,275,277,281}		0	496	f	(1116,670)	f	Glass	f	f	f	156	Juktorus	0	0	f		0	f	f	2
299	2	{297,298,368,484}	Litchmiota	637939981691912202	0	t	(1336,1044)	f	Wood	f	f	f	3443	Otjimna	15	0	f	Litchmiota	637939981691912202	t	f	3
108	2	{106,107,109,113}	Nanhai	899852149360566323	3679	t	(738,767)	f	Glass	f	f	f	3836	Hollowgarde	0	0	f	Nanhai	899852149360566323	f	f	4
404	5	{425}		0	303	f	(1766,738)	f	Tin	f	f	f	858	Salkal	0	0	f		0	f	f	1
1054	2	{1050,1053,1055}	Nokoroth	428949783919460363	0	t	(3699,1989)	f	Copper	f	f	f	2625	Kivuadi	0	0	f	Nokoroth	428949783919460363	f	f	3
222	2	{183,184,185,221,223,224}	Ghad	281967961189908482	400	f	(1296,416)	t	Fur	f	f	f	3326	Brvenijusa	0	0	f	Ghad	281967961189908482	t	f	3
366	0	{363,365,367,368,383,384}	Litchmiota	637939981691912202	0	f	(1406,1111)	f	Glass	f	f	f	3242	Kimnia	15	0	f	Litchmiota	637939981691912202	f	f	2
499	5	{496,505}		0	0	f	(1204,1323)	f	Coal	f	f	f	885	Sarques County	0	0	f	Sarques	353107568547201035	f	f	1
878	2	{872,873,874,877,879,884,891}	jahuva	956593014489362493	2933	f	(3906,315)	f	Livestock	f	f	f	2870	Lilo	0	0	f	jahuva	956593014489362493	f	f	1
761	0	{0}		0	379	t	(3482,268)	f	Grain	f	f	f	3229	Megarina	0	0	f		0	f	f	2
355	2	{354,356}		0	339	t	(2014,576)	f	Wine	f	f	f	4362	Posane	0	0	f		0	f	f	1
1	0	{2,3}		0	381	t	(781,1377)	f	Ivory	f	f	f	3920	Abymna	0	0	f		0	f	f	2
326	9	{324,325,327}		0	124	t	(1802,340)	f	Glass	f	f	f	276	Lampsens	0	0	f		0	f	f	1
27	0	{25,26,29,30,48,49,53}		0	261	f	(803,1134)	t	Fur	f	f	f	4331	Benion	0	0	f		0	f	f	1
335	2	{333,358,432}		0	372	t	(1840,540)	f	Paper	f	f	f	2510	Aytippia	0	0	f		0	f	f	2
412	5	{395,410,411}		0	1113	f	(1636,790)	f	Precious Goods	f	f	f	860	Thespeucia	0	0	f		0	f	f	2
632	2	{629,630,631,633}		0	345	t	(2441,317)	f	Ivory	f	f	f	4054	Cythene	0	0	f		0	f	f	1
489	5	{470,488,490,491}		0	1264	f	(1258,1357)	f	Raw Stone	f	f	f	895	Agrinaclea	0	0	f		0	f	f	1
250	2	{242,243,247,249,251,253}		0	346	f	(1177,803)	t	Ivory	f	f	f	3570	Zuivild	0	0	f		0	f	f	2
374	1	{373,375,458,461}		0	178	f	(1714,864)	f	Ivory	f	f	f	785	Thisruil	0	0	f		0	f	f	1
398	5	{397,399,400,461,462}		0	1004	f	(1721,772)	f	Raw Stone	f	f	f	720	Ilvynyln	0	0	f		0	f	f	2
392	5	{372,391,393,394}		0	1297	f	(1573,830)	f	Tin	f	f	f	697	Teapost	0	0	f		0	f	f	2
393	5	{391,392,394,414,419}		0	1205	f	(1595,803)	f	Spices	f	f	f	671	Starmore	0	0	f		0	f	f	2
243	0	{240,242,244,247,250}		0	389	f	(1186,742)	f	Wool	f	f	f	3730	Strawshire	0	0	f		0	f	f	3
829	5	{823,828,830,831,832}		0	1187	f	(3431,135)	f	Salt	f	f	f	869	Mossmore	0	0	f		0	f	f	1
1016	0	{1013,1015,1017,1032}		0	2771	f	(4019,1393)	f	Fruits	f	f	f	4858	Panteselis	36	0	f		0	f	f	4
375	1	{373,374,376,454,456}		0	119	f	(1683,904)	f	Ivory	f	f	f	534	Gobafidi	0	0	f		0	f	f	3
415	2	{263,264,265,292,293,294,416,417,483}		0	372	f	(1384,817)	f	Livestock	f	f	f	3456	Narakare	0	0	f		0	f	f	1
879	2	{872,878,884,885}	Blindgulf	0	5637	t	(4066,286)	f	Wine	f	f	f	3843	Tabanteki	0	0	f		0	f	f	1
885	2	{879,884,886,887}	Blindgulf	0	5385	t	(4120,387)	f	Tobacco	f	f	f	3745	Kokekola	0	0	f		0	f	f	2
490	5	{470,472,489,491}		0	1155	f	(1240,1368)	t	Tin	f	f	f	883	Mankalane	0	0	f		0	f	f	1
459	2	{455,457,458,460}		0	391	t	(1795,866)	f	Tobacco	f	f	f	3114	Mobane	0	0	f		0	f	f	3
409	5	{407,408,410,411}		0	1133	f	(1676,772)	f	Copper	f	f	f	889	Seria	0	0	f		0	f	f	3
462	2	{398,400,401,402,461}		0	322	t	(1759,763)	f	Tin	f	f	f	4172	Wolmadanha	0	0	f		0	f	f	2
413	5	{414,419,420}		0	1059	f	(1613,776)	t	Gold	f	f	f	899	Genthanie	0	0	f		0	f	f	3
477	2	{166,419,420,478,479,516}		0	325	f	(1559,700)	f	Wood	f	f	f	2855	Babong	0	0	f		0	f	f	4
501	5	{488,502}		0	1270	f	(1249,1332)	f	Coal	f	f	f	802	Quseng	0	0	f		0	f	f	1
468	0	{467,469,470,471}		0	308	t	(1278,1397)	f	Wood	f	f	f	3159	Saldakuwa	0	0	f		0	f	f	1
444	0	{361,387,443,445}	Litchmiota	637939981691912202	0	t	(1521,1298)	f	Wool	f	f	f	4833	Meweng	15	0	f	Litchmiota	637939981691912202	f	f	4
471	0	{467,468,470,472}		0	0	t	(1233,1415)	f	Wood	f	f	f	3418	Namaferu	0	0	f	Sarques	353107568547201035	f	f	1
362	0	{360,363,365,386,387}	Litchmiota	637939981691912202	0	t	(1429,1224)	f	Sugar	f	f	f	3123	Yasousar	15	0	f	Litchmiota	637939981691912202	f	f	2
225	2	{218,219,221,224,226,227}	Ghad	281967961189908482	400	f	(1199,466)	t	Copper	f	f	f	2876	Pokojea	0	0	f	Ghad	281967961189908482	f	f	2
228	2	{223,224,227,229,231,233}	Ghad	281967961189908482	400	f	(1249,499)	t	Tea and Coffee	f	f	f	3631	Taigaa	0	0	f	Ghad	281967961189908482	t	f	1
778	2	{774,777,779,781}	Correlli	293518673417732098	0	t	(2978,94)	f	Salt	f	f	f	2776	Selerobe	0	0	f	Correlli	293518673417732098	f	f	1
447	0	{380,446,448}	Litchmiota	637939981691912202	0	t	(1676,1199)	f	Sugar	t	f	f	3324	Qamatlong	15	0	f	Litchmiota	637939981691912202	f	f	2
1175	0	{1172,1174,1176,1177,1178}	Blindgulf	967635049061163028	0	t	(2504,2392)	f	Paper	f	f	f	4773	Panchun	0	0	f	Blindgulf	967635049061163028	f	f	2
434	2	{289,416,417,418,419,474,516}		0	2275	f	(1494,785)	t	Sugar	f	f	f	3875	Yatori	0	0	f		0	f	f	1
971	2	{970,972,973}	Nokoroth	428949783919460363	0	t	(3886,2628)	f	Tea and Coffee	f	f	f	3614	Cagona	0	0	f	Nokoroth	428949783919460363	f	f	2
251	2	{242,250,252,253,275,276}		0	2317	f	(1100,794)	f	Fruits	f	f	f	3618	Hnífshólar	0	0	f		0	f	f	1
99	0	{81,97,98,100,102,104}	Nanhai	899852149360566323	0	f	(567,785)	t	Grain	f	f	f	3104	Tlothe	0	0	f	Nanhai	899852149360566323	f	f	1
235	2	{155,179,180,229,231,234}		0	1048	f	(1285,576)	f	Rare Wood	f	f	f	3561	Nogoonkh	0	0	f		0	f	f	3
495	1	{494,497}		0	0	t	(1114,1354)	f	Spices	f	f	f	563	Hukuhaba	0	0	f	Sarques	353107568547201035	f	f	2
789	2	{787,788}	Correlli	293518673417732098	0	t	(3241,64)	f	Fur	f	f	f	4136	Mutsutsukawa	0	0	f	Correlli	293518673417732098	f	f	2
500	5	{502,504,506}		0	1229	f	(1231,1312)	f	Raw Stone	f	f	f	665	Lahandja	0	0	f		0	f	f	1
908	0	{876,906,907,910,911}	Blindgulf	0	7312	f	(3694,488)	t	Wood	f	f	f	3656	Atinal	0	0	f		0	f	f	1
491	5	{489,490,492}		0	802	f	(1222,1348)	t	Coal	f	f	f	851	Moine	0	0	f		0	f	f	1
407	5	{399,405,406,408,409,421}		0	1002	f	(1681,749)	t	Salt	f	f	f	747	Vulembu	0	0	f		0	f	f	2
408	5	{407,409,410,420,421}		0	1101	f	(1651,758)	f	Silver	f	f	f	842	Allanrys	0	0	f		0	f	f	1
618	1	{616,619,620}	Tusail	844640695868194927	0	t	(666,2515)	f	Ivory	f	f	f	575	Jirozmian	23	0	f	Tusail	844640695868194927	f	f	2
420	2	{408,410,413,419,421,477,478,479}		0	396	f	(1604,713)	f	Salt	f	f	f	2977	Okashapi	0	0	f		0	f	f	2
72	0	{70,71,73,74,75,94,95}		0	259	f	(589,895)	f	Wool	f	f	f	4644	Oshirara	0	0	f		0	f	f	4
237	2	{233,234,236,238,239}	Ghad	281967961189908482	400	f	(1219,625)	f	Copper	f	f	f	3959	Ruhenhengeri	0	0	f	Ghad	281967961189908482	t	f	3
349	5	{346,350}		0	1007	f	(1912,511)	f	Copper	f	f	f	704	Changchong	0	0	f		0	f	f	1
1093	0	{965,969,1092}		0	284	f	(3312,1533)	f	Sugar	f	f	f	4531	Meishui	0	0	f		0	f	f	3
357	2	{356,358,359}		0	365	t	(1946,619)	f	Sugar	f	f	f	2592	Khairmani	0	0	f		0	f	f	3
430	0	{312,427,428,429,431,42}		0	331	f	(1741,594)	f	Grain	f	f	f	3825	Kangwon	0	0	f		0	f	f	2
457	2	{455,456,458,459}		0	392	f	(1791,913)	f	Glass	f	f	f	2628	Hamsu	0	0	f		0	f	f	2
481	2	{164,165,307,480,482,483}		0	363	f	(1568,625)	f	Livestock	f	f	f	3967	Taewang	0	0	f		0	f	f	1
621	1	{0}		0	137	t	(499,2659)	f	Fish	f	f	f	781	Sinuihung	0	0	f		0	f	f	1
769	0	{768}	Blindgulf	0	6956	t	(3552,516)	f	Ivory	f	f	f	3478	Khepeset	0	0	f		0	f	f	1
339	5	{336,337,338,340,350}		0	1036	f	(1885,542)	f	Silver	f	f	f	670	Nurhakisla	0	0	f		0	f	f	1
857	9	{855,856,858,859,862}	Blindgulf	0	566	t	(3663,162)	f	Glass	f	f	f	283	Vestvöllur	0	0	f		0	f	f	1
968	0	{967,989,990,1003}		0	346	t	(3567,1323)	f	Cotton	f	f	f	4446	As	0	0	f		0	f	f	2
341	5	{342}		0	1005	f	(1854,513)	f	Silver	f	f	f	669	Sasiyyah	0	0	f		0	f	f	2
287	2	{271,273,274,284,286}		0	392	f	(970,826)	f	Wood	f	f	f	3789	Mirut	0	0	f		0	f	f	2
989	0	{968,990,991}		0	362	t	(3632,1271)	f	Wood	f	f	f	3971	Wadireg	0	0	f		0	f	f	2
131	2	{129,132}		0	349	f	(882,803)	f	Copper	f	f	f	4034	Choinuur	0	0	f		0	f	f	2
316	9	{317,318}		0	101	t	(1678,414)	f	Precious Goods	f	f	f	198	Pingrao	0	0	f		0	f	f	4
1038	2	{1026,1037,1039,1041,1042}		0	398	f	(3816,1728)	f	Wood	f	f	f	3457	Kumaraha	0	0	f		0	f	f	3
126	7	{113,124,125,127,128,285,433}	Nanhai	899852149360566323	0	f	(886,668)	t	Rare Wood	f	f	f	237	Legstead	0	0	f	Nanhai	899852149360566323	f	f	1
182	2	{177,178,180,181,183}	Ghad	281967961189908482	400	f	(1386,479)	t	Chocolate	f	f	f	3776	Karlsborg	0	0	f	Ghad	281967961189908482	t	f	2
1143	0	{1129,1131,1132,1142,1144}	Khokand	905858887926816768	0	t	(2790,1755)	f	Spices	f	f	f	4802	Rakawald	18	0	f	Khokand	905858887926816768	f	f	3
537	0	{536,538,549,552}	Tusail	844640695868194927	0	t	(1219,2198)	f	Tobacco	f	f	f	4935	Telefuiva	23	0	f	Tusail	844640695868194927	f	f	4
145	0	{144,146,147,255,256}	Litchmiota	637939981691912202	0	t	(1156,1006)	f	Livestock	t	f	f	3068	Marlimar	15	0	f	Litchmiota	637939981691912202	t	f	3
520	2	{512,523}	Tusail	844640695868194927	0	t	(454,1962)	f	Copper	t	f	f	4122	Adankum	23	0	f	Tusail	844640695868194927	f	f	1
278	7	{232,277}	Ghad	281967961189908482	650	t	(1145,562)	f	Glass	f	f	f	157	Marhovec	0	0	f	Ghad	281967961189908482	f	f	2
1018	0	{1017,1019,1029,1030}		0	2003	t	(4136,1546)	f	Fur	f	f	f	4129	Dawnglen	36	0	f		0	f	f	3
1169	5	{1153,1154,1170}	Blindgulf	967635049061163028	0	f	(2889,2246)	f	Tin	f	f	f	647	Okairuru	0	0	f	Blindgulf	967635049061163028	f	f	1
526	2	{524,525}	Tusail	844640695868194927	0	t	(495,2176)	f	Copper	f	f	f	3826	Niupia	23	0	f	Tusail	844640695868194927	f	f	1
945	0	{944,946,957,958,959}	Khokand	905858887926816768	0	t	(3060,1370)	f	Rare Wood	f	f	f	3410	Gioba	18	0	f	Khokand	905858887926816768	f	f	2
197	9	{196,198,201}		0	196	t	(1188,263)	f	Fur	f	f	f	185	Antberge	0	0	f		0	f	f	2
1040	2	{1023,1024,1039,1041}		0	1843	t	(3780,1886)	f	Tin	f	f	f	2597	Borgueu	36	0	f		0	f	f	1
118	7	{116,117,121}	Nanhai	899852149360566323	0	t	(639,553)	t	Coal	f	f	f	248	Vumbavua	0	0	f	Nanhai	899852149360566323	f	f	1
1045	2	{1008,1009,1044,1046}	New Crea	692089085690380288	30	f	(3517,1611)	t	Fur	f	f	t	4253	Tattingstein	17	0	f	New Crea	692089085690380288	f	f	2
986	1	{983,984,985,987,988}	Nokoroth	428949783919460363	0	f	(3988,2987)	f	Paper	f	f	f	644	Grallón	0	0	f	Nokoroth	428949783919460363	f	f	1
510	0	{509}		0	363	t	(556,1442)	f	Cotton	f	f	f	4034	Qahanieh	0	0	f		0	f	f	2
893	0	{890,892,894,803,804}		0	1651	f	(3901,477)	t	Wool	f	f	f	4812	Götkreis	0	0	f		0	f	f	2
1083	5	{1078,1084,1085,1105}		0	1293	f	(3186,1906)	f	Salt	f	f	f	747	Khanayah	0	0	f		0	f	f	3
845	9	{844,846,851,852}		0	119	t	(3533,188)	f	Ivory	f	f	f	246	As	0	0	f		0	f	f	3
926	0	{923}	Blindgulf	0	7362	t	(3325,967)	f	Fish	f	f	f	3681	Seafurah	0	0	f		0	f	f	1
712	2	{702,710,711,713,714,1217}		0	399	f	(2657,796)	f	Iron	f	f	f	3536	Khorranab	0	0	f		0	f	f	2
627	2	{626,628,629}		0	333	t	(2349,313)	f	Iron	f	f	f	3636	Alaroft	0	0	f		0	f	f	1
665	0	{664,666,678,679,680}		0	390	t	(2770,441)	f	Wood	f	f	f	4519	Iliborlu	0	0	f		0	f	f	1
218	2	{216,217,219,225,226}	Ghad	281967961189908482	650	t	(1152,461)	f	Fish	t	f	f	3813	Plunjoji	0	0	f	Ghad	281967961189908482	t	f	2
1052	2	{1050,1051,1053,1057,1059}		0	395	f	(3648,1958)	f	Fruits	f	f	f	2784	Tanimotu	0	0	f		0	f	f	1
1030	0	{1017,1018,1029,1031,1032}		0	2484	f	(4053,1521)	f	Wood	f	f	f	4012	Mapuapara	36	0	f		0	f	f	3
718	0	{682,717}		0	323	t	(2515,659)	f	Fur	f	f	f	4139	Utusi	0	0	f		0	f	f	2
21	0	{17,18,20,22}		0	397	t	(650,1163)	t	Wood	f	f	f	4177	Fetofesia	0	0	f		0	f	f	2
1060	2	{1058,1059,1061,1065}		0	345	t	(3504,1998)	f	Glass	f	f	f	2631	Fohi	0	0	f		0	f	f	1
315	2	{302,314}		0	305	t	(1638,445)	f	Paper	f	f	f	4472	Geelide	0	0	f		0	f	f	4
705	0	{704,706}		0	257	t	(2860,990)	f	Glass	f	f	f	4576	Seafave	0	0	f		0	f	f	3
732	2	{730,731,733,738}	Correlli	293518673417732098	0	t	(3186,389)	t	Livestock	f	f	f	4395	Arisyoun	0	0	f	Correlli	293518673417732098	f	f	1
843	5	{837,842,844,846}		0	1197	f	(3499,164)	f	Coal	f	f	f	680	Tekatiratai	0	0	f		0	f	f	4
148	2	{147,149,255,296}	Litchmiota	637939981691912202	0	f	(1235,954)	f	Grain	f	f	f	2828	Hamchaek	15	0	f	Litchmiota	637939981691912202	t	f	4
673	0	{669,672,674,675,676,722}		0	307	f	(2991,598)	f	Tobacco	f	f	f	3034	Faleamalo	0	0	f		0	f	f	1
841	5	{839,840,847,848}		0	1239	t	(3486,96)	f	Fish	f	f	f	826	A'ufaga	0	0	f		0	f	f	3
1079	7	{1068,1070,1078,1080,1082}		0	117	f	(3297,1976)	f	Paper	f	f	f	276	Ivorgarde	0	0	f		0	f	f	4
167	0	{164,165,166,168,173,476}		0	308	f	(1505,641)	t	Fruits	f	f	f	4136	Glockrath	0	0	f		0	f	f	1
122	7	{119,121,123}		0	176	t	(733,495)	f	Spices	f	f	f	225	Charward	0	0	f		0	f	f	2
559	7	{556,558,560}		0	139	t	(1147,2542)	f	Silk	f	f	f	290	Aerahaben	0	0	f		0	f	f	3
567	5	{566,568,569}		0	1117	t	(1170,2767)	f	Coal	f	f	f	833	Flammore	0	0	f		0	f	f	1
695	5	{687,694,696}		0	1015	f	(2830,706)	f	Spices	f	f	f	804	Fljot	0	0	f		0	f	f	4
614	1	{610,613,615,619}	Tusail	844640695868194927	0	f	(772,2569)	f	Paper	f	f	f	542	Jokulsarhlio	23	0	f	Tusail	844640695868194927	f	f	3
1170	5	{1153,1168,1169}	Blindgulf	967635049061163028	0	t	(2857,2226)	f	Coal	f	f	f	698	Tenedo	0	0	f	Blindgulf	967635049061163028	f	f	1
1130	0	{1098,1099,1100,1128,1129,1131}	Khokand	905858887926816768	0	f	(2862,1668)	f	Cotton	f	f	f	4181	Velipa	18	0	f	Khokand	905858887926816768	f	f	1
802	2	{801,803,810,811}	Correlli	293518673417732098	0	t	(3271,119)	f	Rare Wood	f	f	f	3093	Tonnéte	0	0	f	Correlli	293518673417732098	f	f	1
527	0	{528,529,530}	Tusail	844640695868194927	0	t	(684,2277)	f	Wood	f	f	f	3971	Calacadis	23	0	f	Tusail	844640695868194927	f	f	1
377	1	{376,378,453}	Litchmiota	637939981691912202	0	f	(1676,1001)	f	Glass	f	f	f	600	Sakarout	15	0	f	Litchmiota	637939981691912202	f	f	3
972	2	{971,973,979}	Nokoroth	428949783919460363	0	t	(3892,2752)	f	Wood	f	f	f	4323	Zamostile	0	0	f	Nokoroth	428949783919460363	f	f	4
172	5	{158,168,170,173,175}	Ghad	281967961189908482	400	f	(1467,661)	f	Spices	f	f	f	705	Dalkrókur	0	0	f	Ghad	281967961189908482	f	f	3
191	9	{189,190,192}	Ghad	281967961189908482	650	t	(1314,216)	f	Fur	t	f	f	234	Maloji	0	0	f	Ghad	281967961189908482	t	f	1
442	1	{441}	Litchmiota	637939981691912202	0	t	(1829,1548)	f	Precious Goods	f	f	f	728	Danzibanyatsi	15	0	f	Litchmiota	637939981691912202	f	f	4
1163	5	{1162,1164}	Blindgulf	967635049061163028	0	f	(2988,2306)	f	Coal	f	f	f	819	Abenastina	0	0	f	Blindgulf	967635049061163028	f	f	1
518	2	{519,521,522}	Tusail	844640695868194927	0	t	(328,1966)	f	Wood	f	f	f	4306	Portus	23	0	f	Tusail	844640695868194927	f	f	3
897	0	{887,888,896,898,899}		0	2888	t	(4072,580)	f	Grain	f	f	f	3379	Hokitakere	0	0	f		0	f	f	2
905	0	{877,892,904,906}	Blindgulf	0	6316	f	(3854,459)	f	Glass	f	f	f	3158	Yelalabuga	0	0	f		0	f	f	1
113	7	{108,109,114,120,124,126,127}	Nanhai	899852149360566323	0	t	(778,679)	f	Glass	f	f	f	214	Liquasa	0	0	f	Nanhai	899852149360566323	f	f	1
630	2	{628,629,631,632}		0	355	t	(2367,387)	f	Fruits	f	f	f	3114	Hagbarosholmr	0	0	f		0	f	f	1
652	2	{650,651,653,655}		0	325	t	(2662,90)	f	Chocolate	f	f	f	3011	Hrafnstoptir	0	0	f		0	f	f	3
1210	2	{1209}	Nokoroth	428949783919460363	0	t	(3355,2648)	f	Fruits	f	f	f	3190	Sinra	0	0	f	Nokoroth	428949783919460363	f	f	2
184	9	{183,185,222}	Ghad	281967961189908482	650	t	(1379,389)	f	Fish	t	f	f	215	Setrias	0	0	f	Ghad	281967961189908482	f	f	1
1078	7	{1070,1077,1079,1082,1083,1084}	New Crea	692089085690380288	231	f	(3240,1938)	f	Rare Wood	f	f	f	170	Eskiholt	15	0	f	New Crea	692089085690380288	f	f	3
660	0	{659,661,662}		0	287	t	(2869,306)	f	Grain	f	f	f	4934	Riocarí	0	0	f		0	f	f	4
1144	0	{1142,1143,1145,1147}	Khokand	905858887926816768	0	t	(2694,1791)	t	Cotton	f	f	f	4313	Atrans	18	0	f	Khokand	905858887926816768	f	f	2
445	0	{381,385,386,44,446}	Litchmiota	637939981691912202	0	t	(1539,1231)	f	Ivory	t	f	f	4955	Lethagonami	15	0	f	Litchmiota	637939981691912202	f	f	3
28	0	{9,10,12,19,29}		0	292	f	(781,1226)	t	Fruits	f	f	f	4015	Nulriel	0	0	f		0	f	f	3
798	9	{795,796,797,799}		0	228	t	(3635,22)	f	Fish	f	f	f	267	Messimezia	6	0	f		0	f	f	1
735	2	{734,736,741}	Correlli	293518673417732098	0	t	(3033,288)	f	Glass	f	f	f	3846	Tuder	0	0	f	Correlli	293518673417732098	f	f	1
1059	2	{1051,1052,1057,1058,1060,1061}		0	311	f	(3589,1931)	f	Grain	f	f	f	3694	Immia	0	0	f		0	f	f	4
578	7	{577,579}		0	126	t	(1012,2896)	f	Coal	f	f	f	238	Makourama	0	0	f		0	f	f	2
132	2	{131,133,286,288}		0	315	f	(900,812)	t	Livestock	f	f	f	4097	Pago	0	0	f		0	f	f	2
648	2	{644,645,647}		0	338	t	(2702,283)	f	Precious Goods	f	f	f	3112	Ejimare	0	0	f		0	f	f	2
713	2	{711,712,714}		0	368	t	(2614,799)	f	Wood	f	f	f	3810	Caudium	0	0	f		0	f	f	1
22	0	{21,23,24}		0	315	t	(686,1150)	f	Wool	f	f	f	4641	Armorica	0	0	f		0	f	f	1
33	0	{8,31,32,34,35}		0	315	f	(956,1217)	f	Glass	f	f	f	3819	Emporiae	0	0	f		0	f	f	1
921	0	{919,920,922}	Blindgulf	0	6512	t	(3508,679)	f	Livestock	f	f	f	3256	Ycemire	0	0	f		0	f	f	2
670	0	{668,669,671,728}		0	359	f	(3019,477)	f	Wool	f	f	f	4649	Ostium	0	0	f		0	f	f	3
1108	5	{1101,1102,1107,1109}		0	1203	f	(3013,1843)	f	Raw Stone	f	f	f	698	Sinope	0	0	f		0	f	f	1
1156	5	{1154,1155,1157}		0	1022	t	(3015,2262)	f	Salt	f	f	f	627	Selymbria	0	0	f		0	f	f	2
629	2	{627,628,630,632}		0	308	t	(2389,355)	f	Spices	f	f	f	3453	Cannabiaca	0	0	f		0	f	f	4
1069	5	{1067,1068}		0	1012	f	(3373,1980)	f	Silver	f	f	f	823	Vinovium	0	0	f		0	f	f	1
622	1	{0}		0	157	t	(454,2896)	f	Paper	f	f	f	795	Catania	0	0	f		0	f	f	2
1081	5	{1080,1082,1111,1112,1117,1118}		0	1126	f	(3184,2010)	f	Silver	f	f	f	609	Seveyungri	0	0	f		0	f	f	4
631	2	{630,632,633}		0	327	t	(2405,391)	f	Salt	f	f	f	3964	Anarechny	0	0	f		0	f	f	3
1206	2	{1204,1205}	Blindgulf	967635049061163028	0	t	(3078,2937)	f	Spices	t	f	f	4380	Thalareth	0	0	f	Blindgulf	967635049061163028	t	f	1
1157	5	{1156}	Blindgulf	967635049061163028	0	t	(3060,2300)	f	Salt	f	f	f	700	Hydgia	0	0	f	Blindgulf	967635049061163028	f	f	4
1164	5	{1163,1165}	Blindgulf	967635049061163028	0	f	(2934,2297)	f	Spices	f	f	f	840	Hytin	0	0	f	Blindgulf	967635049061163028	f	f	1
368	0	{299,366,367,369,383,484}	Litchmiota	637939981691912202	0	t	(1384,1055)	f	Tobacco	f	f	f	4200	Arakuru	15	0	f	Litchmiota	637939981691912202	f	f	2
159	0	{158,160,161,174,175,178}	Ghad	281967961189908482	400	f	(1415,578)	f	Wood	f	f	f	4112	Zakhobil	0	0	f	Ghad	281967961189908482	t	f	3
384	1	{363,364,366,383,383,385}	Litchmiota	637939981691912202	0	f	(1444,1105)	f	Spices	f	f	f	769	Kaiškuva	15	0	f	Litchmiota	637939981691912202	f	f	4
440	1	{438,439,465,466}	Litchmiota	637939981691912202	0	t	(2077,1503)	f	Spices	f	f	f	587	Mesane	15	0	f	Litchmiota	637939981691912202	f	f	2
1023	2	{1022,1024,1040}		0	2536	t	(3877,1962)	t	Chocolate	f	f	f	3212	Liquasa	36	0	f		0	f	f	1
744	2	{0}	Correlli	293518673417732098	0	t	(3129,122)	f	Wine	f	f	f	3046	Amphireth	0	0	f	Correlli	293518673417732098	f	f	3
585	5	{580,581,584,586,611,612}	Tusail	844640695868194927	0	f	(916,2713)	f	Tin	f	f	f	711	Boyrem	23	0	f	Tusail	844640695868194927	f	f	2
264	5	{265,289,415}		0	254	f	(1420,918)	f	Raw Stone	f	f	f	821	Sogusi	0	0	f		0	f	f	2
1211	0	{0}	Nokoroth	428949783919460363	0	t	(3240,2324)	f	Rare Wood	f	f	f	4252	Hafgrimsfjoror	0	0	f	Nokoroth	428949783919460363	f	f	3
383	1	{366,368,369,371,378,382,384}	Litchmiota	637939981691912202	0	f	(1435,1021)	f	Paper	f	f	f	619	Ähtäkumpu	15	0	f	Litchmiota	637939981691912202	f	f	3
1022	2	{1021,1023,1024,1025}		0	2747	t	(3958,1908)	t	Glass	f	f	f	2717	Stijki	36	0	f		0	f	f	2
1158	5	{1159,1162}	Blindgulf	967635049061163028	0	t	(3056,2317)	f	Raw Stone	f	f	f	632	Posegia	0	0	f	Blindgulf	967635049061163028	f	f	1
1020	2	{1019,1021,1026,1027}		0	362	t	(4064,1715)	f	Wood	f	f	f	3794	Puritin	0	0	f		0	f	f	2
837	5	{836,838,842,843}		0	1050	f	(3474,171)	f	Raw Stone	f	f	f	641	Belipis	0	0	f		0	f	f	1
924	0	{925}	Blindgulf	0	8472	t	(3458,936)	f	Fish	f	f	f	4236	Kaakrahnath	0	0	f		0	f	f	1
208	2	{207,209,212,213}	Ghad	281967961189908482	400	f	(1057,369)	f	Tea and Coffee	f	f	f	2698	Zothout	0	0	f	Ghad	281967961189908482	t	f	2
1015	0	{1013,1014,1016,1017}		0	2090	t	(4054,1377)	f	Grain	f	f	f	4285	Thelor	36	0	f		0	f	f	2
836	5	{835,837,44}		0	1273	t	(3478,187)	f	Iron	f	f	f	725	Tempemon	0	0	f		0	f	f	3
894	0	{889,890,893,895,903}	Blindgulf	0	9004	f	(3971,490)	t	Paper	f	f	f	4502	Liqucadis	0	0	f		0	f	f	1
690	2	{689,691,706,707}		0	360	t	(2956,778)	f	Iron	f	f	f	3514	Tethton	0	0	f		0	f	f	1
1089	7	{1074,1087,1088,1090,1094}		0	163	f	(3213,1643)	t	Glass	f	f	f	159	Paciris	0	0	f		0	f	f	1
796	9	{795,797,798}		0	143	t	(3633,46)	f	Fish	f	f	f	230	Levialean	0	0	f		0	f	f	3
764	0	{0}		0	302	t	(3550,350)	f	Tea and Coffee	f	f	f	3178	Aciolis	0	0	f		0	f	f	2
832	5	{828,829,831,833,840}		0	1237	f	(3454,130)	f	Raw Stone	f	f	f	673	Sireria	0	0	f		0	f	f	1
763	0	{0}		0	395	t	(3583,321)	f	Fur	f	f	f	3254	Liquiri	0	0	f		0	f	f	3
773	2	{774,775}	Correlli	293518673417732098	0	t	(2952,166)	f	Wood	f	f	f	3918	Tsuloch	0	0	f	Correlli	293518673417732098	f	f	3
770	0	{0}	Blindgulf	0	6286	t	(3474,520)	f	Cotton	f	f	f	3143	Salania	0	0	f		0	f	f	1
667	0	{663,664,666,668,667,676}		0	395	f	(2891,463)	f	Paper	f	f	f	4039	Aciopis	0	0	f		0	f	f	2
999	0	{998,1000,1011,1012,1013,1014}		0	349	f	(3798,1371)	f	Paper	f	f	f	4505	Berylora	0	0	f		0	f	f	2
708	0	{706,707}		0	391	t	(2965,1015)	f	Paper	f	f	f	3591	Riverem	0	0	f		0	f	f	1
324	9	{320,323,326,327,328,329}		0	177	f	(1816,353)	f	Glass	f	f	f	278	Abyrey	0	0	f		0	f	f	3
1111	5	{1081,1082,1112,1113}		0	1096	f	(3136,1935)	f	Iron	f	f	f	713	Scylor	0	0	f		0	f	f	1
569	5	{565,566,567,570,571}		0	1290	f	(1179,2745)	f	Coal	f	f	f	683	Belilean	0	0	f		0	f	f	2
767	0	{766}		0	316	t	(3403,405)	f	Fish	f	f	f	4123	Levialore	0	0	f		0	f	f	2
512	2	{511,513}		0	334	t	(556,1069)	f	Livestock	f	f	f	4344	Ashamon	0	0	f		0	f	f	1
1087	5	{1074,1086,1088,1089,1103}		0	1231	f	(3218,1778)	t	Spices	f	f	f	861	Microd	0	0	f		0	f	f	1
721	0	{719,720,722,723}		0	338	t	(3157,612)	f	Sugar	f	f	f	4117	Taltahrar	0	0	f		0	f	f	2
649	9	{650,651}		0	158	t	(2590,31)	f	Ivory	f	f	f	250	Vazulzak	0	0	f		0	f	f	3
121	7	{118,119,122}		0	138	t	(686,468)	t	Silk	f	f	f	165	Tunkhudduk	0	0	f		0	f	f	3
187	9	{186,188,194,195}	Ghad	281967961189908482	650	t	(1303,308)	f	Glass	t	f	f	247	Outiva	0	0	f	Ghad	281967961189908482	f	f	4
955	0	{949,951,954,956,963,964}		0	2971	f	(3280,1363)	f	Spices	f	f	f	3976	Demike	0	0	f		0	f	f	3
1182	0	{1160,1161,1162,1167,1181,1183,1185,1186}	Blindgulf	967635049061163028	0	f	(2991,2442)	f	Wool	f	f	f	3845	Psychrinitida	0	0	f	Blindgulf	967635049061163028	f	f	4
970	2	{971,973,974}	Nokoroth	428949783919460363	0	t	(3966,2579)	f	Spices	f	f	f	3613	Rutago	0	0	f	Nokoroth	428949783919460363	f	f	1
216	2	{213,214,217,218}	Ghad	281967961189908482	650	t	(1100,439)	f	Wine	t	f	f	2618	Valkeani	0	0	f	Ghad	281967961189908482	t	f	3
1122	7	{1120,1121,1123}	Nokoroth	428949783919460363	952	t	(3150,2203)	t	Fish	f	f	f	220	Tylamnus	0	0	f	Nokoroth	428949783919460363	t	f	2
106	2	{103,105,107,108,109}	Nanhai	899852149360566323	0	f	(684,760)	t	Sugar	f	f	f	3138	Lofale	0	0	f	Nanhai	899852149360566323	f	f	2
364	0	{363,384,385,386}	Litchmiota	637939981691912202	0	f	(1476,1170)	f	Wood	f	f	f	4508	Mneesayr	15	0	f	Litchmiota	637939981691912202	f	f	1
997	0	{991,992,996,998,1000}		0	2849	f	(3744,1292)	f	Paper	f	f	f	4223	Thuriliki	0	0	f		0	f	f	2
755	2	{754,756,757,758}	Correlli	293518673417732098	0	t	(3289,292)	f	Salt	f	f	f	3084	Ellaba	0	0	f	Correlli	293518673417732098	f	f	1
552	0	{536,537,549,551,553,596}	Tusail	844640695868194927	0	f	(1204,2223)	f	Tobacco	f	f	f	3953	Nakkuss	23	0	f	Tusail	844640695868194927	f	f	1
1021	2	{1020,1022,1025,1026}		0	2453	t	(3994,1823)	t	Grain	f	f	f	2762	Salaren	36	0	f		0	f	f	1
922	0	{920,921}	Blindgulf	0	7064	t	(3481,758)	f	Cotton	f	f	f	3532	Buye	0	0	f		0	f	f	2
1179	0	{1171,1172,1178,1180,1190}	Blindgulf	967635049061163028	0	f	(2694,2415)	f	Sugar	f	f	f	3804	Quellton	0	0	f	Blindgulf	967635049061163028	f	f	1
1212	0	{0}	Nokoroth	428949783919460363	0	t	(3348,2326)	f	Fur	f	f	f	3404	Vsekolov	0	0	f	Nokoroth	428949783919460363	f	f	3
486	9	{65}	Ghad	281967961189908482	650	t	(1498,61)	f	Glass	t	f	f	284	Bilbilis	0	0	f	Ghad	281967961189908482	f	f	1
574	7	{573,575,587}		0	155	f	(1060,2716)	t	Coal	f	f	f	152	Zukkross	0	0	f		0	f	f	3
1126	7	{1114,1115,1123,1124,1125,1127}	New Crea	692089085690380288	0	t	(2909,1996)	t	Glass	f	f	f	282	Maganango	18	0	f	New Crea	692089085690380288	f	f	1
1138	0	{1137,1139,1151}	Khokand	905858887926816768	0	t	(2536,1566)	f	Wool	f	f	f	4294	Chaszuth	18	0	f	Khokand	905858887926816768	f	f	3
884	2	{878,879,885,886,891}	Blindgulf	0	8006	f	(4027,349)	f	Wine	f	f	f	4003	Thyrespiae	0	0	f		0	f	f	2
892	0	{877,890,891,893,904,905}	Blindgulf	0	8980	f	(3890,434)	f	Cotton	f	f	f	4490	Carthage	0	0	f		0	f	f	2
88	5	{87,89,90}		0	1246	f	(369,826)	f	Coal	f	f	f	893	Mamo	0	0	f		0	f	f	1
658	2	{565,657}		0	304	t	(2794,151)	f	Tea and Coffee	f	f	f	3641	Mlankindu	0	0	f		0	f	f	1
717	0	{683,714,716,718}		0	254	t	(2563,661)	f	Wool	f	f	f	3184	Biharari	0	0	f		0	f	f	1
952	0	{950,951,953,967}		0	261	t	(3427,1264)	t	Grain	f	f	f	4880	Jira	0	0	f		0	f	f	2
1076	5	{1074,1075,1077,1084,1085,1086}		0	1192	f	(3274,1848)	f	Precious Stones	f	f	f	864	Apayo	0	0	f		0	f	f	2
685	5	{684,686,696,697,698,715}		0	1107	f	(2752,661)	f	Spices	f	f	f	698	Kamudo	0	0	f		0	f	f	1
1086	5	{1074,1076,1085,1087,1103}		0	1021	f	(3238,1811)	t	Salt	f	f	f	668	Dawnbury	0	0	f		0	f	f	2
795	9	{796,798}		0	114	t	(3590,20)	f	Precious Goods	f	f	f	201	Termina	0	0	f		0	f	f	1
1121	7	{1120,1122}		0	149	t	(3301,2160)	f	Spices	f	f	f	177	Krslav	0	0	f		0	f	f	3
1090	0	{961,1089,1091,1092,1094}		0	325	f	(3209,1555)	t	Paper	f	f	f	4438	Democaea	0	0	f		0	f	f	3
1105	5	{1083,1085,1103,1104,1106}		0	1122	f	(3162,1841)	f	Tin	f	f	f	790	Myrini	0	0	f		0	f	f	2
62	0	{61,63,66,67}		0	387	f	(778,947)	t	Wool	f	f	f	3685	Lamesus	0	0	f		0	f	f	2
327	9	{324,326,328}		0	174	t	(1813,333)	f	Fur	f	f	f	287	Kyratrea	0	0	f		0	f	f	2
345	5	{330,331,344,346,347}		0	1198	f	(1888,466)	f	Raw Stone	f	f	f	698	Lampsomenus	0	0	f		0	f	f	1
29	0	{9,26,27,28,30,32}		0	394	f	(819,1197)	t	Cotton	f	f	f	3955	Oncheron	0	0	f		0	f	f	1
668	0	{663,667,669,670,728,729}		0	267	t	(2974,430)	f	Paper	f	f	f	4443	Cumespiae	0	0	f		0	f	f	1
666	0	{664,665,667,676,677,678}		0	355	f	(2815,496)	f	Paper	f	f	f	3388	Myndasae	0	0	f		0	f	f	3
1112	5	{1081,1111,1113,1115,1116,1117}		0	1111	f	(3130,1998)	f	Raw Stone	f	f	f	698	Acomenion	0	0	f		0	f	f	2
848	9	{841,847,849}		0	199	t	(3496,88)	f	Fur	f	f	f	171	Cumakros	0	0	f		0	f	f	4
1145	0	{1144,1146,1147}	Khokand	905858887926816768	0	t	(2615,1823)	f	Wood	f	f	f	3288	Lefkanthus	18	0	f	Khokand	905858887926816768	f	f	3
800	2	{752,759,801,803,804}	Correlli	293518673417732098	0	f	(3260,153)	f	Grain	f	f	f	3371	Boroupoli	0	0	f	Correlli	293518673417732098	f	f	1
158	0	{157,159,172,175,290}	Ghad	281967961189908482	400	f	(1415,632)	f	Tea and Coffee	f	f	f	4381	Rhypada	0	0	f	Ghad	281967961189908482	t	f	2
937	0	{934,936,938,1147}	Khokand	905858887926816768	0	t	(2617,1417)	f	Fruits	f	f	f	3790	Phliesos	18	0	f	Khokand	905858887926816768	f	f	1
940	0	{939,941,942,1098,1134,1135,1136}	Khokand	905858887926816768	0	f	(2758,1528)	t	Glass	f	f	f	3821	Onchapetra	18	0	f	Khokand	905858887926816768	f	f	1
946	0	{945,947,957}	Khokand	905858887926816768	0	t	(3089,1269)	f	Fur	f	f	f	3053	Leontinitida	18	0	f	Khokand	905858887926816768	f	f	1
941	0	{933,939,940,942}	Khokand	905858887926816768	0	f	(2797,1507)	t	Wool	f	f	f	3764	Kruba	18	0	f	Khokand	905858887926816768	f	f	2
1131	0	{1098,1129,1130,1132,1143}	Khokand	905858887926816768	0	f	(2833,1701)	t	Livestock	f	f	f	3274	Gelaclea	18	0	f	Khokand	905858887926816768	f	f	2
978	2	{973,977,979,981,982}	Nokoroth	428949783919460363	0	f	(3922,2828)	f	Livestock	f	f	f	3415	Elaticus	0	0	f	Nokoroth	428949783919460363	f	f	1
435	1	{436,437}	Litchmiota	637939981691912202	0	t	(1867,1440)	f	Ivory	f	f	f	729	Architanas	15	0	f	Litchmiota	637939981691912202	f	f	3
1165	5	{1162,1164,1166,1167,1168}	Blindgulf	967635049061163028	0	f	(2892,2338)	f	Silver	f	f	f	828	Hierinope	0	0	f	Blindgulf	967635049061163028	f	f	3
298	2	{259,296,297,299,484}	Litchmiota	637939981691912202	0	f	(1307,983)	f	Copper	f	f	f	3828	Jazin	15	0	f	Litchmiota	637939981691912202	t	f	1
980	1	{879,981}	Nokoroth	428949783919460363	0	t	(3796,2886)	f	Glass	f	f	f	643	Kwano	0	0	f	Nokoroth	428949783919460363	f	f	2
855	9	{854,856,857,858}		0	128	t	(3613,94)	f	Fur	f	f	f	165	Aigous	0	0	f		0	f	f	1
779	2	{776,777,778,780,781,782}	Correlli	293518673417732098	0	t	(3025,90)	f	Tobacco	f	f	f	3042	Ekanbron	0	0	f	Correlli	293518673417732098	f	f	1
643	2	{642,644,645,646}		0	300	t	(2583,281)	f	Livestock	f	f	f	3667	Gythagoria	0	0	f		0	f	f	2
115	7	{111,112,116,118,119}	Nanhai	899852149360566323	0	f	(675,612)	f	Paper	f	f	f	265	Qetika	0	0	f	Nanhai	899852149360566323	f	f	1
1198	2	{1188,1189,1197,1201,1202}	Blindgulf	967635049061163028	0	f	(2811,2770)	f	Sugar	f	f	f	2996	Soha	0	0	f	Blindgulf	967635049061163028	t	f	1
438	1	{439,440}	Litchmiota	637939981691912202	0	t	(2050,1476)	f	Glass	f	f	f	769	Kilanga	15	0	f	Litchmiota	637939981691912202	f	f	2
332	2	{313,322,333,431}		0	330	f	(1769,518)	f	Wood	f	f	f	3633	Himos	0	0	f		0	f	f	2
1085	5	{1076,1083,1084,1086,1003,1005}		0	1208	f	(3220,1843)	t	Raw Stone	f	f	f	884	Losse	0	0	f		0	f	f	2
65	9	{483}	Ghad	281967961189908482	650	t	(1521,40)	f	Ivory	t	f	f	171	Odessus	0	0	f	Ghad	281967961189908482	t	f	3
522	2	{518,519,521,524,525}	Tusail	844640695868194927	0	t	(333,2083)	f	Grain	t	f	f	3225	Kollsvik	23	0	f	Tusail	844640695868194927	f	f	2
1058	2	{1057,1059,60}		0	2578	t	(3546,2012)	f	Tobacco	f	f	f	3632	Noma	36	0	f		0	f	f	1
1103	5	{1085,1086,1087,1088,1102,1104,1105}		0	1036	f	(3177,1780)	f	Tin	f	f	f	893	Olamum	0	0	f		0	f	f	1
793	5	{791,792,794}	Reasonable Nation Name	293518673417732098	1295	t	(3419,37)	f	Silver	f	f	f	702	Nokapi	0	0	f	Reasonable Nation Name	293518673417732098	f	f	1
772	0	{0}	Blindgulf	0	9292	t	(3376,525)	f	Rare Wood	f	f	f	4646	Nsabasena	0	0	f		0	f	f	1
290	0	{157,158,291,292,474}		0	292	f	(1411,688)	f	Wood	f	f	f	4681	Katyros	0	0	f		0	f	f	2
844	9	{836,837,843,845,846}		0	115	t	(3499,185)	f	Fish	f	f	f	252	Thasseron	0	0	f		0	f	f	1
1041	2	{1038,1039,1040,1042,1047,150}	New Crea	692089085690380288	221	t	(3729,1836)	t	Salt	f	f	f	2654	Lobashe	15	0	f	New Crea	692089085690380288	f	f	2
573	7	{560,574,587,588,590}		0	127	f	(1071,2639)	t	Silk	f	f	f	224	Metens	0	0	f		0	f	f	2
794	5	{792,793}		0	1011	t	(3390,52)	f	Raw Stone	f	f	f	842	Moleporobe	0	0	f		0	f	f	2
936	0	{927,934,935,937}	Khokand	905858887926816768	0	t	(2585,1332)	t	Wool	f	f	f	4322	Massipolis	18	0	f	Khokand	905858887926816768	f	f	2
959	0	{944,945,958,960,961}		0	342	f	(3065,1454)	f	Cotton	f	f	f	3944	Qetithing	0	0	f		0	f	f	4
95	0	{71,72,94,96,97,98}		0	301	f	(634,857)	f	Glass	f	f	f	4528	Omudu	0	0	f		0	f	f	3
698	5	{697,699,715,1215,1216}		0	1115	f	(2758,727)	f	Precious Stones	f	f	f	780	Lotrowe	0	0	f		0	f	f	4
152	0	{151,153,154,292,293}		0	353	f	(1296,805)	f	Fruits	f	f	f	4829	Okahadive	0	0	f		0	f	f	2
702	2	{692,700,701,703,710,712}		0	361	f	(2756,783)	t	Livestock	f	f	f	3464	Dulevise	0	0	f		0	f	f	2
635	2	{634,636}		0	364	t	(2380,175)	f	Salt	f	f	f	2939	Rehovi	0	0	f		0	f	f	1
133	2	{66,132,134,137,286,288}		0	371	f	(891,895)	t	Spices	f	f	f	2725	Oshidja	0	0	f		0	f	f	2
178	0	{157,158,159,160,177,179,180,182}		0	2462	f	(1390,529)	f	Glass	f	f	f	3811	Beaufort	0	0	f		0	f	f	1
944	0	{932,943,945,959,960,1097}	Khokand	905858887926816768	0	t	(2997,1435)	t	Glass	f	f	f	4870	Ruststar	18	0	f	Khokand	905858887926816768	f	f	1
1132	0	{1098,1131,1134,1134,1142,1143}	Khokand	905858887926816768	0	f	(2757,1674)	t	Fur	f	f	f	3300	Orodorm	18	0	f	Khokand	905858887926816768	f	f	3
928	0	{927,929,930,931,934,935}	Khokand	905858887926816768	0	t	(2725,1280)	t	Wool	f	f	f	3738	Pihane	18	0	f	Khokand	905858887926816768	f	f	3
1098	0	{940,942,1097,1099,1130,1131,1132,1134}	Khokand	905858887926816768	0	f	(2844,1548)	t	Wood	f	f	f	3797	Wintermoor	18	0	f	Khokand	905858887926816768	f	f	3
947	0	{946,948,957}	Khokand	905858887926816768	0	t	(3125,1267)	f	Wool	f	f	f	4624	Kaliz	18	0	f	Khokand	905858887926816768	f	f	1
385	1	{364,381,382,384,386,445}		0	713	f	(1514,1186)	f	Precious Stones	f	f	f	620	Solengwa	15	0	f		0	f	f	4
277	7	{232,241,276,278,279,281,281}	Ghad	281967961189908482	650	t	(1093,594)	f	Ivory	t	f	f	218	Sasotaten	0	0	f	Ghad	281967961189908482	t	f	2
984	1	{977,983,985,986}	Nokoroth	428949783919460363	0	t	(4152,2901)	f	Dyes	f	f	f	778	Rouyonne	0	0	f	Nokoroth	428949783919460363	f	f	3
814	2	{810,813,815,816}	Correlli	293518673417732098	0	f	(3350,144)	f	Grain	f	f	f	3535	Paphateia	0	0	f	Correlli	293518673417732098	f	f	3
233	2	{227,228,231,232,234,237,238}	Ghad	281967961189908482	400	f	(1219,567)	f	Wood	f	f	f	3880	Raelellón	0	0	f	Ghad	281967961189908482	f	f	1
977	2	{975,976,978,982,983,984}	Nokoroth	428949783919460363	0	t	(4059,2826)	f	Wine	f	f	f	4418	Andanea	0	0	f	Nokoroth	428949783919460363	t	f	1
816	2	{808,813,814,815,817,818,819,820}	Correlli	293518673417732098	0	t	(3386,157)	f	Tobacco	f	f	f	4060	Scarmouth	0	0	f	Correlli	293518673417732098	f	f	1
628	2	{626,627,629,630}		0	346	t	(2333,367)	f	Wood	f	f	f	2669	Meyokabei	0	0	f		0	f	f	1
939	0	{933,934,938,940,941,1136}	Khokand	905858887926816768	0	f	(2693,1469)	t	Wool	f	f	f	3375	Cálma	18	0	f	Khokand	905858887926816768	f	f	1
891	2	{877,878,884,886,890,892}	Blindgulf	0	7612	f	(3922,369)	f	Iron	f	f	f	3806	Grimbay	0	0	f		0	f	f	1
560	7	{558,559,561,573,590}		0	177	t	(1132,2603)	t	Paper	f	f	f	272	Westwall	0	0	f		0	f	f	2
653	9	{651,652,654,655}		0	146	t	(2713,43)	f	Fur	f	f	f	178	Freyview	0	0	f		0	f	f	3
1004	0	{966,967,1003,1005,1006,1007}		0	277	f	(3450,1400)	t	Cotton	f	f	f	4179	Bayhollow	0	0	f		0	f	f	3
1116	5	{1112,1115,1117,1118,1119,1120}		0	1281	f	(3112,2073)	f	Coal	f	f	f	883	Frostvalley	0	0	f		0	f	f	3
645	2	{643,644,646,647,648}		0	306	f	(2623,241)	f	Fruits	f	f	f	3418	Smallstrand	0	0	f		0	f	f	1
595	0	{553,555,557,594,596,597}	Tusail	844640695868194927	0	f	(1147,2329)	f	Cotton	f	f	f	4785	Bergessonne	23	0	f	Tusail	844640695868194927	f	f	3
654	9	{653,655,656,657}		0	160	t	(2734,45)	f	Fur	f	f	f	263	Limestar	0	0	f		0	f	f	2
765	0	{0}		0	315	t	(3493,380)	f	Cotton	f	f	f	4972	Southborough	0	0	f		0	f	f	1
51	0	{49,50,52,135,136}		0	368	f	(846,1044)	f	Tobacco	f	f	f	4435	Arrowstrand	0	0	f		0	f	f	2
25	0	{23,24,26,27,53}		0	294	f	(749,1123)	f	Tobacco	f	f	f	4198	Borville	0	0	f		0	f	f	2
63	0	{52,54,61,62,64,66}		0	287	f	(790,952)	t	Wool	f	f	f	4404	Ironfield	0	0	f		0	f	f	3
1025	2	{1021,1022,1024,1026,1039}		0	375	f	(3918,1782)	f	Fur	f	f	f	3643	Silenttown	0	0	f		0	f	f	4
40	7	{39,41,142}		0	164	t	(1125,1075)	f	Rare Wood	f	f	f	226	Silvershore	0	0	f		0	f	f	2
1125	7	{1124,1126,1153}		0	147	t	(2844,2054)	f	Coal	f	f	f	286	Avinia	0	0	f		0	f	f	2
576	7	{575,577,579,580}		0	156	t	(1028,2812)	t	Coal	f	f	f	183	Virtos	0	0	f		0	f	f	3
166	0	{165,167,168,476,477,478}		0	299	f	(1541,673)	f	Fruits	f	f	f	4138	Sagoza	0	0	f		0	f	f	4
791	5	{790,792,793}		0	1229	t	(3428,16)	f	Coal	f	f	f	798	Bacourt	0	0	f		0	f	f	1
300	0	{162,163,301,302,483}		0	268	t	(1573,497)	f	Ivory	f	f	f	4288	Cololimar	0	0	f		0	f	f	2
514	2	{513,515}		0	345	t	(524,1003)	f	Livestock	f	f	f	3611	Grelly	0	0	f		0	f	f	1
135	7	{51,52,64,134,136}		0	102	f	(844,990)	f	Paper	f	f	f	170	Sarsart	0	0	f		0	f	f	3
155	0	{154,156,179,234,235,245,246}		0	290	f	(1291,657)	t	Rare Wood	f	f	f	4285	Vinmont	0	0	f		0	f	f	1
138	7	{44,47,50,136,137,139}		0	161	f	(938,1021)	f	Rare Wood	f	f	f	270	Puroux	0	0	f		0	f	f	1
464	1	{436,437}	Litchmiota	637939981691912202	0	t	(1993,1449)	f	Spices	f	f	f	690	Himarnacia	15	0	f	Litchmiota	637939981691912202	f	f	3
619	1	{613,614,615,616,618,620}	Tusail	844640695868194927	0	f	(731,2560)	f	Precious Stones	f	f	f	756	Atrophy	23	0	f	Tusail	844640695868194927	f	f	3
194	9	{187,193,195,220}	Ghad	281967961189908482	400	f	(1244,324)	f	Ivory	f	f	f	283	Onyxpeak	0	0	f	Ghad	281967961189908482	t	f	2
1178	0	{1172,1176,1177,1179,1190,1191}	Blindgulf	967635049061163028	0	f	(2619,2417)	f	Livestock	f	f	f	4417	Jara	0	0	f	Blindgulf	967635049061163028	f	f	2
1214	0	{0}	Nokoroth	428949783919460363	0	t	(3438,2182)	f	Rare Wood	f	f	f	3936	Trinilores	0	0	f	Nokoroth	428949783919460363	f	f	1
280	7	{277,279,281,282,433}	Ghad	281967961189908482	400	f	(1015,637)	t	Glass	f	f	f	186	Pavlosse	0	0	f	Ghad	281967961189908482	f	f	2
985	1	{984,986,988}	Nokoroth	428949783919460363	0	t	(4144,2999)	f	Glass	f	f	f	520	Quickpeak	0	0	f	Nokoroth	428949783919460363	f	f	1
1187	2	{1184,1185,1186,1188,1204}	Blindgulf	967635049061163028	0	t	(3099,2754)	f	Glass	t	f	f	4493	Salamento	0	0	f	Blindgulf	967635049061163028	t	f	2
506	1	{498,503,504,505}	Litchmiota	637939981691912202	0	t	(1222,1258)	f	Fish	f	f	f	502	Kubuye	15	0	f	Litchmiota	637939981691912202	f	f	2
597	0	{535,594,595,596,598,599}	Tusail	844640695868194927	0	f	(1080,2268)	t	Livestock	f	f	f	3804	Trasmo	23	0	f	Tusail	844640695868194927	f	f	2
781	2	{778,779,782}	Correlli	293518673417732098	0	t	(3012,55)	f	Glass	f	f	f	3348	Sarillos	0	0	f	Correlli	293518673417732098	f	f	1
889	0	{886,887,888,890,894,895}	Blindgulf	0	7870	f	(4014,466)	t	Wood	f	f	f	3935	Bonetrail	0	0	f		0	f	f	3
119	7	{114,115,120,121,122,123}	Nanhai	899852149360566323	0	f	(697,551)	t	Precious Goods	f	f	f	260	Sarfannfik	0	0	f	Nanhai	899852149360566323	f	f	1
153	0	{151,152,154,246,248}		0	353	f	(1267,787)	t	Fruits	f	f	f	4274	Whisperpeak	0	0	f		0	f	f	1
134	7	{64,66,133,135,136}		0	171	f	(859,940)	t	Paper	f	f	f	256	Lowbellow	0	0	f		0	f	f	2
130	0	{0}		0	321	f	(801,841)	f	Wood	f	f	f	4026	Thingorge	0	0	f		0	f	f	2
124	7	{113,120,123,125,126}	Testlandia	293518673417732098	142	t	(850,562)	t	Silk	f	f	f	269	Pola	0	0	f	Testlandia	293518673417732098	f	f	2
1029	0	{1018,1019,1028,1030,1031}		0	2109	f	(4059,1578)	f	Tea and Coffee	f	f	f	3579	Talonhallow	36	0	f		0	f	f	2
180	2	{178,179,181,182,229,230,235}		0	333	f	(1323,531)	f	Glass	f	f	f	2806	Copperstead	0	0	f		0	f	f	2
169	5	{168,170,171,474,475}		0	1005	f	(1460,711)	f	Copper	f	f	f	618	Barebank	0	0	f		0	f	f	2
925	0	{924}	Blindgulf	0	8492	t	(3424,1012)	f	Wood	f	f	f	4246	Rerio	0	0	f		0	f	f	4
261	5	{258,260,262,294}		0	1138	f	(1352,916)	f	Raw Stone	f	f	f	789	Rejanes	0	0	f		0	f	f	3
295	2	{149,150,151,257,294,296}		0	344	f	(1289,909)	f	Fruits	f	f	f	4278	Carcos	0	0	f		0	f	f	3
260	5	{258,259,261,262,266}		0	1157	f	(1370,940)	f	Raw Stone	f	f	f	686	Jinoral	0	0	f		0	f	f	1
291	0	{154,156,157,290,292}		0	310	f	(1359,702)	f	Grain	f	f	f	3193	Guacan	0	0	f		0	f	f	2
285	7	{126,128}		0	120	f	(916,733)	f	Coal	f	f	f	223	Ditos	0	0	f		0	f	f	1
923	0	{926}	Blindgulf	0	7278	t	(3321,810)	f	Grain	f	f	f	3639	Priguaque	0	0	f		0	f	f	1
700	5	{699,701,702,1216}		0	1299	f	(2792,767)	t	Raw Stone	f	f	f	714	Cuyatal	0	0	f		0	f	f	3
74	0	{72,73,75,76}		0	355	t	(533,922)	f	Sugar	f	f	f	3361	Aposonate	0	0	f		0	f	f	2
351	2	{331,348,352,353}		0	382	t	(1951,475)	f	Paper	f	f	f	3151	Atijutla	0	0	f		0	f	f	2
854	9	{851,852,853,855,856}		0	173	t	(3584,94)	f	Fish	f	f	f	195	Mipiles	0	0	f		0	f	f	2
93	2	{77,78,86,87,92}		0	347	t	(394,929)	f	Fur	f	f	f	3017	Jalacho	0	0	f		0	f	f	1
827	5	{817,826,828,834,835}		0	1211	t	(3433,187)	f	Spices	f	f	f	696	Volnola	0	0	f		0	f	f	1
680	0	{678,679,681,684}		0	386	t	(2662,533)	f	Grain	f	f	f	4905	Aguanahu	0	0	f		0	f	f	2
682	0	{681,683,717,718}		0	288	t	(2547,560)	f	Livestock	f	f	f	4130	Cojulupe	0	0	f		0	f	f	1
1106	5	{1104,1105,1107}		0	1254	f	(3145,1893)	f	Raw Stone	f	f	f	728	Ponlants	0	0	f		0	f	f	1
1068	5	{1067,1069,1079,1080}		0	1177	f	(3355,2009)	f	Tin	f	f	f	778	Hepmagne	0	0	f		0	f	f	4
561	7	{560,562,570,572}		0	130	t	(1206,2637)	t	Coal	f	f	f	237	Clerbiens	0	0	f		0	f	f	3
11	0	{3,10,12,13}		0	302	t	(733,1298)	t	Fish	f	f	f	3354	Oqaattaq	0	0	f		0	f	f	2
740	2	{739,741,742,745,746}	Correlli	293518673417732098	0	f	(3127,250)	f	Iron	f	f	f	2936	Landbrunn	0	0	f	Correlli	293518673417732098	f	f	2
1065	7	{1060,1063,1064,1066,1067,1071}	New Crea	692089085690380288	0	t	(3461,1938)	f	Fish	f	f	f	275	Xalacoco	18	0	f	New Crea	692089085690380288	f	f	2
1128	0	{1100,1101,1127,1129,1130}	Khokand	905858887926816768	0	t	(2875,1758)	f	Tea and Coffee	f	f	f	4499	Fonnipporp	18	0	f	Khokand	905858887926816768	f	f	3
1072	5	{1063,1070,1071,1073,1075}	New Crea	692089085690380288	559	f	(3389,1870)	f	Tin	f	f	f	718	Gerasweg	12	0	f	New Crea	692089085690380288	f	f	1
1168	5	{1167,1170,1171}	Blindgulf	967635049061163028	0	t	(2826,2295)	f	Silver	f	f	f	789	Thistlehelm	0	0	f	Blindgulf	967635049061163028	f	f	2
579	7	{576,577,578,580,581}		0	240	t	(961,2799)	f	Precious Goods	f	f	f	210	Freelmorg	34	0	f		0	f	f	3
437	1	{435,436,464}	Litchmiota	637939981691912202	0	t	(1960,1449)	f	Precious Stones	f	f	f	521	Miggiddoz	15	0	f	Litchmiota	637939981691912202	f	f	2
1181	0	{1167,1180,1182,1190}	Blindgulf	967635049061163028	0	f	(2858,2516)	f	Rare Wood	f	f	f	3026	Glostos	0	0	f	Blindgulf	967635049061163028	f	f	2
1172	0	{1171,1173,1174,1175,1178,1179}	Blindgulf	967635049061163028	0	t	(2628,2277)	f	Wood	f	f	f	3127	Napaluitsup	0	0	f	Blindgulf	967635049061163028	f	f	3
933	0	{931,932,934,939,941,942}	Khokand	905858887926816768	0	f	(2792,1429)	t	Ivory	f	f	f	3116	Canterster	18	0	f	Khokand	905858887926816768	f	f	1
400	5	{399,398,401,405,425,462}		0	0	f	(1748,749)	f	Coal	f	f	f	754	Chitecas	0	0	f	Orienta	913474777488973934	f	f	4
1061	2	{1051,1059,1060,1062,1064,1065}		0	1784	f	(3526,1886)	f	Copper	f	f	f	2991	Jiutelende	0	0	f		0	f	f	4
1148	0	{1147,1150,1151,1152}	Khokand	905858887926816768	0	f	(2543,1733)	f	Cotton	f	f	f	4668	Mummadogh	18	0	f	Khokand	905858887926816768	f	f	3
1063	7	{1062,1064,1065,1071,1072,1073}	New Crea	692089085690380288	139	f	(3452,1816)	t	Ivory	f	f	f	200	Wigglegate	16	0	f	New Crea	692089085690380288	t	f	1
1196	2	{1189,1190,1191,1195,1197}	Blindgulf	967635049061163028	0	f	(2658,2644)	f	Grain	f	f	f	4267	Lebridge	0	0	f	Blindgulf	967635049061163028	t	f	3
783	2	{780,782,784}	Correlli	293518673417732098	0	t	(3067,42)	f	Iron	f	f	f	2839	Greenwall	0	0	f	Correlli	293518673417732098	f	f	4
1209	2	{1210}	Nokoroth	428949783919460363	0	t	(3348,2727)	f	Sugar	f	f	f	4346	Penjachuca	0	0	f	Nokoroth	428949783919460363	f	f	2
612	1	{583,584,585,610,611,613}	Tusail	844640695868194927	0	f	(817,2655)	f	Glass	f	f	f	511	Keenfa	23	0	f	Tusail	844640695868194927	f	f	2
354	2	{353,355,356}		0	395	t	(1989,549)	f	Fish	f	f	f	3546	Chesmore	0	0	f		0	f	f	1
799	9	{797,798}		0	192	t	(3643,16)	f	Glass	f	f	f	290	Sparkwall	6	0	f		0	f	f	1
320	9	{319,321,323,324,325,326}		0	101	f	(1762,412)	f	Fur	f	f	f	189	Autumncester	0	0	f		0	f	f	4
909	0	{0}		0	272	t	(3651,459)	f	Wood	f	f	f	4421	Brighstone	0	0	f		0	f	f	3
503	5	{487,488,502,506}	Litchmiota	637939981691912202	0	t	(1264,1291)	f	Copper	f	f	f	688	Ersten	15	0	f	Litchmiota	637939981691912202	f	f	4
236	2	{234,237,239,245}	Ghad	281967961189908482	400	f	(1251,628)	f	Tobacco	f	f	f	3907	Wiwiya	0	0	f	Ghad	281967961189908482	t	f	2
623	1	{0}		0	106	t	(88,3078)	f	Precious Goods	f	f	f	602	Sirapaluk	0	0	f		0	f	f	2
792	5	{790,791,793,794}		0	1034	t	(3389,27)	f	Salt	f	f	f	822	Nutaarhivik	0	0	f		0	f	f	1
709	0	{703,704,710,711}		0	282	t	(2713,904)	f	Fur	f	f	f	3422	Kuumtu	0	0	f		0	f	f	3
46	0	{31,32,34,36,37,45,47,48}		0	300	f	(918,1147)	t	Wool	f	f	f	4859	Garmis	0	0	f		0	f	f	1
1019	2	{1018,1020,1027,1028,1029}		0	329	t	(4012,1670)	t	Fur	f	f	f	3247	Plumewatch	0	0	f		0	f	f	1
78	2	{76,77,79,86,93}		0	320	f	(443,916)	f	Grain	f	f	f	4223	Finkipplurg	0	0	f		0	f	f	2
1082	5	{1078,1079,1080,1081,1111}		0	1065	f	(3195,1969)	f	Raw Stone	f	f	f	855	Fili	0	0	f		0	f	f	2
853	9	{849,850,851,854}		0	197	t	(3559,92)	f	Fur	f	f	f	235	Dintindeck	0	0	f		0	f	f	2
16	0	{13,15,17,18,19}		0	335	f	(637,1237)	f	Wood	f	f	f	4483	Périssons	0	0	f		0	f	f	1
1155	5	{1123,1124,1154,1156}		0	1230	t	(3027,2226)	f	Raw Stone	f	f	f	719	Caluçon	0	0	f		0	f	f	1
358	2	{335,336,357,359}		0	364	t	(1879,594)	f	Tea and Coffee	f	f	f	4110	Gailkirchen	0	0	f		0	f	f	3
856	9	{852,854,855,857}		0	115	t	(3613,153)	f	Fur	f	f	f	233	Ansholz	0	0	f		0	f	f	4
24	0	{22,23,25,26}		0	289	f	(729,1141)	f	Sugar	f	f	f	4041	Macvan	0	0	f		0	f	f	1
948	0	{947,949,956,957}		0	280	t	(3193,1285)	f	Cotton	f	f	f	4212	Mullindoran	0	0	f		0	f	f	2
835	5	{827,834,836}		0	1056	t	(3456,189)	f	Copper	f	f	f	789	Dikkerk	0	0	f		0	f	f	2
1171	0	{1167,1668,1172,1179,1180}	Blindgulf	967635049061163028	0	t	(2712,2322)	f	Tobacco	f	f	f	3235	Llalot	0	0	f	Blindgulf	967635049061163028	f	f	1
85	5	{79,83,84,86}	Nanhai	899852149360566323	0	t	(432,812)	f	Salt	f	f	f	768	Arikaraka	0	0	f	Nanhai	899852149360566323	f	f	1
806	2	{757,758,759,805,807}	Correlli	293518673417732098	0	f	(3316,229)	f	Chocolate	f	f	f	4183	Spalion	0	0	f	Correlli	293518673417732098	f	f	4
487	1	{473,488,503}	Litchmiota	637939981691912202	0	t	(1287,1278)	f	Spices	f	f	f	581	Saldanus	15	0	f	Litchmiota	637939981691912202	f	f	1
1120	7	{1115,1116,1119,1121,1122,1123}	New Crea	692089085690380288	0	t	(3110,2115)	t	Precious Goods	f	f	f	237	Budakovec	18	0	f	New Crea	692089085690380288	f	f	2
1207	2	{1208}	Nokoroth	428949783919460363	0	t	(3319,2945)	f	Ivory	f	f	f	3078	Neuschlag	0	0	f	Nokoroth	428949783919460363	f	f	3
599	0	{533,593,594,597,598,600}	Tusail	844640695868194927	0	f	(1019,2302)	t	Grain	f	f	f	4321	Trujirito	23	0	f	Tusail	844640695868194927	f	f	3
221	2	{185,186,195,219,222,224,225}	Ghad	281967961189908482	400	f	(1251,398)	f	Paper	f	f	f	3414	Knokberge	0	0	f	Ghad	281967961189908482	f	f	1
215	0	{0}	Ghad	281967961189908482	650	t	(909,475)	f	Wool	t	f	f	3522	Mallaza	0	0	f	Ghad	281967961189908482	t	f	3
1185	0	{1182,1183,1184,1186,1187}	Blindgulf	967635049061163028	0	f	(3036,2606)	f	Livestock	f	f	f	4822	Rethyndra	0	0	f	Blindgulf	967635049061163028	t	f	2
625	1	{624}	Litchmiota	637939981691912202	0	t	(2272,1503)	f	Glass	f	f	f	646	Geythis	15	0	f	Litchmiota	637939981691912202	f	f	1
988	1	{985,986,987}	Nokoroth	428949783919460363	0	t	(3942,3090)	f	Paper	f	f	f	666	Xhycyrë	0	0	f	Nokoroth	428949783919460363	f	f	3
724	0	{671,672,723,725,727,728}	Correlli	293518673417732098	0	f	(3098,506)	t	Sugar	f	f	f	3969	Vöcklabühel	0	0	f	Correlli	293518673417732098	f	f	1
582	1	{581,583,584}	Tusail	844640695868194927	0	t	(785,2761)	f	Ivory	f	f	f	755	Tammme	23	0	f	Tusail	844640695868194927	f	f	3
102	2	{97,99,103,104,105}	Nanhai	899852149360566323	0	f	(628,776)	t	Tin	f	f	f	3128	Betatra	0	0	f	Nanhai	899852149360566323	f	f	2
1051	2	{1049,1050,1052,1059,1061,1062}	New Crea	692089085690380288	791	f	(3558,1875)	f	Iron	f	f	f	4133	Amdenz	10	0	f	New Crea	692089085690380288	f	f	2
253	2	{249,250,251,252,254,256,267,289}		0	331	f	(1120,866)	t	Chocolate	f	f	f	4255	Spreitenbach	0	0	f		0	f	f	3
642	2	{641,643,646}		0	371	t	(2554,247)	f	Glass	f	f	f	3828	Appenlach	0	0	f		0	f	f	2
79	2	{75,76,78,80,84,85,86}		0	310	f	(450,866)	f	Fur	f	f	f	2984	Poyslach	0	0	f		0	f	f	2
92	2	{87,91,93}		0	391	t	(353,929)	f	Wine	f	f	f	3327	Valès	0	0	f		0	f	f	4
901	0	{895,899,900,902,917}	Blindgulf	0	9390	f	(3935,637)	t	Livestock	f	f	f	4771	Dornnau	0	0	f		0	f	f	4
1133	0	{1132,1134,1135,1141,1142}	Khokand	905858887926816768	0	f	(2745,1627)	t	Fur	f	f	f	4180	Bullajt	18	0	f	Khokand	905858887926816768	f	f	2
634	2	{635,636,637}		0	309	t	(2443,191)	f	Paper	f	f	f	3461	Kaisasina	0	0	f		0	f	f	2
433	7	{125,126,279,280,282}	Ghad	281967961189908482	650	t	(952,601)	t	Silk	t	f	f	293	Eskilfors	0	0	f	Ghad	281967961189908482	f	f	3
307	0	{303,306,308,309,480,481,482}		0	319	f	(1609,605)	f	Cotton	f	f	f	3482	Tsarasirabe	0	0	f		0	f	f	1
661	0	{659,660,662,663,664}		0	276	t	(2815,331)	f	Tobacco	f	f	f	4433	Fandrabava	0	0	f		0	f	f	3
1024	2	{1022,1023,1025,1039,1040}		0	312	f	(3888,1827)	t	Copper	f	f	f	3015	Wokagee	0	0	f		0	f	f	1
454	2	{375,376,455,456}		0	348	t	(1735,949)	f	Iron	f	f	f	4141	Lesliaj	0	0	f		0	f	f	1
1005	0	{965,966,969,1004,1006,1093}		0	366	f	(3387,1452)	t	Livestock	f	f	f	3887	Kryeliku	0	0	f		0	f	f	2
864	2	{860,861,863,865,866,874,875}	Blindgulf	0	7746	f	(3780,247)	f	Rare Wood	f	f	f	3873	Ebreichdeck	0	0	f		0	f	f	3
38	0	{37,39,42}		0	293	t	(1093,1152)	f	Wool	f	f	f	3850	Ermoulonghi	0	0	f		0	f	f	2
572	5	{561,570,571}		0	1290	f	(1154,2659)	f	Raw Stone	f	f	f	852	Prevedri	0	0	f		0	f	f	3
681	0	{680,682,683,684}		0	350	t	(2610,553)	f	Fur	f	f	f	4123	Polipoi	0	0	f		0	f	f	2
1007	0	{1002,1003,1004,1006,1008}		0	323	f	(3499,1449)	f	Rare Wood	f	f	f	4612	Vavamanitra	0	0	f		0	f	f	2
1124	7	{1123,1125,1126,1153,1155}		0	106	f	(2977,2109)	t	Glass	f	f	f	183	Antsolaona	0	0	f		0	f	f	1
41	7	{39,40,42,43,44,142}		0	158	f	(1075,1069)	f	Ivory	f	f	f	208	Amparatsetra	0	0	f		0	f	f	2
165	0	{164,166,167,478,480,481}		0	344	f	(1539,641)	t	Livestock	f	f	f	4133	Berovombe	0	0	f		0	f	f	1
571	5	{569,570,572}		0	1033	f	(1170,2707)	f	Precious Goods	f	f	f	640	Antafolotra	0	0	f		0	f	f	4
252	2	{251,253,274,289}		0	365	f	(1078,835)	f	Chocolate	f	f	f	2735	Vohimavony	0	0	f		0	f	f	3
605	2	{601,604,606,607}	Tusail	844640695868194927	0	f	(841,2421)	t	Fruits	f	f	f	2962	Lustenstein	23	0	f	Tusail	844640695868194927	f	f	1
583	1	{582,584,612,613}		0	596	t	(745,2704)	f	Dyes	f	f	f	541	Halstraten	34	0	f		0	f	f	1
80	2	{75,79,81,82,84,98}	Nanhai	899852149360566323	0	f	(488,855)	t	Tobacco	f	f	f	3173	Livasekë	0	0	f	Nanhai	899852149360566323	f	f	1
117	2	{116,118}	Nanhai	899852149360566323	595	t	(623,623)	f	Grain	f	f	f	3167	Terben	0	0	f	Nanhai	899852149360566323	f	f	1
1055	2	{1053,1054,1056}	Nokoroth	428949783919460363	0	t	(3697,2128)	f	Tobacco	f	f	f	2772	Wolfstadt	0	0	f	Nokoroth	428949783919460363	f	f	2
1119	7	{1080,1116,1118,1120}		0	225	f	(3180,2106)	t	Glass	f	f	f	289	Torstraten	13	0	f		0	f	f	1
581	5	{579,580,582,584,585}	Tusail	844640695868194927	0	t	(909,2761)	f	Raw Stone	f	f	f	688	Brugleeuw	23	0	f	Tusail	844640695868194927	f	f	3
198	9	{193,196,197,199,201}	Ghad	281967961189908482	400	f	(1188,279)	f	Precious Goods	f	f	f	193	Manratok	0	0	f	Ghad	281967961189908482	t	f	1
188	9	{187}	Ghad	281967961189908482	650	t	(1348,283)	f	Spices	f	f	f	256	Sleetdrift	0	0	f	Ghad	281967961189908482	t	f	1
594	0	{557,591,593,595,597,599}	Tusail	844640695868194927	0	f	(1102,2333)	f	Fruits	f	f	f	3356	Tangerschau	23	0	f	Tusail	844640695868194927	f	f	3
283	7	{274,275,281,282,284}	Ghad	281967961189908482	400	f	(1017,749)	t	Coal	f	f	f	159	Zaravila	0	0	f	Ghad	281967961189908482	t	f	4
616	2	{604,606,615,617,618,619}	Tusail	844640695868194927	0	t	(724,2473)	f	Grain	t	f	f	3218	Vounina	23	0	f	Tusail	844640695868194927	f	f	3
1186	2	{1182,1185,1187,1188,1189,1190}	Blindgulf	967635049061163028	0	f	(2995,2610)	f	Fur	f	f	f	2748	Tynea	0	0	f	Blindgulf	967635049061163028	t	f	2
1050	2	{1041,1047,1049,1051,1052,1053,1054}	Nokoroth	428949783919460363	0	t	(3650,1863)	f	Livestock	f	f	f	4004	Dillaas	0	0	f	Nokoroth	428949783919460363	f	f	3
363	0	{362,364,365,366,384,386}		0	2128	f	(1429,1183)	f	Glass	f	f	f	3874	Ongwema	15	0	f		0	f	f	2
112	2	{109,111,114,115}	Nanhai	899852149360566323	0	f	(702,697)	f	Sugar	f	f	f	4160	Kugjun	0	0	f	Nanhai	899852149360566323	f	f	2
935	0	{927,928,934,936}	Khokand	905858887926816768	0	f	(2691,1354)	t	Tobacco	f	f	f	4642	Kalengrad	18	0	f	Khokand	905858887926816768	f	f	2
328	9	{324,327,329,330}		0	128	t	(1849,389)	f	Spices	f	f	f	271	Rrogolenë	0	0	f		0	f	f	1
342	5	{338,341,344,346,350}		0	1119	f	(1874,493)	f	Raw Stone	f	f	f	802	Vërkopi	0	0	f		0	f	f	2
671	0	{669,670,672,724,728}		0	257	f	(3026,526)	f	Grain	f	f	f	4687	Pasekë	0	0	f		0	f	f	2
1042	2	{1037,1038,1041,1043,1047,1048}		0	383	f	(3751,1733)	t	Grain	f	f	f	3330	Ansten	0	0	f		0	f	f	2
272	0	{269,270,271,273}		0	354	f	(981,907)	t	Precious Goods	f	f	f	3065	Kirchdenz	0	0	f		0	f	f	2
123	7	{119,120,122,124}		0	140	t	(792,515)	t	Rare Wood	f	f	f	175	Floliada	0	0	f		0	f	f	3
66	0	{62,63,64,67,133,134}		0	294	f	(803,920)	f	Glass	f	f	f	4596	Metarni	0	0	f		0	f	f	1
128	2	{126,127,129,285}		0	364	f	(891,758)	t	Wood	f	f	f	4144	Tsalangwe	0	0	f		0	f	f	3
170	5	{168,169,171,172}		0	1073	f	(1460,686)	f	Coal	f	f	f	742	Mitunte	0	0	f		0	f	f	1
142	7	{41,44,140,141,143,144}		0	170	f	(1051,1037)	f	Precious Goods	f	f	f	235	Domamasi	0	0	f		0	f	f	4
257	5	{258,259,294,295,296}		0	1165	f	(1325,929)	f	Silver	f	f	f	683	Blalaomo	0	0	f		0	f	f	1
87	5	{86,88,90,91,92,93}		0	1194	f	(387,859)	f	Precious Stones	f	f	f	842	Mponera	0	0	f		0	f	f	1
950	0	{949,951,952}		0	328	t	(3323,1264)	f	Fish	f	f	f	3671	Poonbilli	0	0	f		0	f	f	1
918	0	{902,904,913,917}	Blindgulf	0	9866	f	(3850,569)	t	Wool	f	f	f	4933	Mamumarë	0	0	f		0	f	f	4
12	0	{10,11,13,19,28}		0	267	f	(738,1255)	t	Glass	f	f	f	4664	Šipojaš	0	0	f		0	f	f	1
511	2	{512}		0	326	t	(565,1107)	f	Grain	f	f	f	4079	Bijeldor	0	0	f		0	f	f	1
679	0	{665,680}		0	399	t	(2707,492)	f	Cotton	f	f	f	3653	Caska	0	0	f		0	f	f	3
1114	5	{1113,1115,1126,1127}		0	1289	f	(3022,1994)	t	Coal	f	f	f	710	Nieuwport	0	0	f		0	f	f	2
42	0	{37,38,39,41,42}		0	294	f	(1082,1098)	f	Ivory	f	f	f	4705	Westden	0	0	f		0	f	f	1
322	9	{317,321,332,333}		0	140	f	(1735,450)	f	Precious Goods	f	f	f	151	Sassarence	0	0	f		0	f	f	2
15	0	{13,14,16,17}		0	287	t	(621,1249)	f	Cotton	f	f	f	4063	Bitoraele	0	0	f		0	f	f	1
125	7	{124,126,433}		0	156	t	(891,601)	t	Spices	f	f	f	263	Thyochenza	0	0	f		0	f	f	1
519	2	{518,522}	Tusail	844640695868194927	0	t	(274,1966)	f	Livestock	f	f	f	3748	Mutuabo	23	0	f	Tusail	844640695868194927	f	f	3
84	5	{79,80,82,83,85}	Nanhai	899852149360566323	0	f	(461,837)	f	Raw Stone	f	f	f	620	Aviçon	0	0	f	Nanhai	899852149360566323	f	f	2
389	5	{370,372,388,390,485}		0	209	f	(1521,871)	f	Spices	f	f	f	655	Camagal	15	0	f		0	f	f	1
817	5	{816,818,826,827}	Correlli	293518673417732098	0	t	(3409,198)	f	Iron	f	f	f	689	Dammuide	0	0	f	Correlli	293518673417732098	f	f	2
388	5	{370,389,463,485}	Litchmiota	637939981691912202	0	f	(1507,884)	f	Gold	f	f	f	672	Chabezi	15	0	f	Litchmiota	637939981691912202	f	f	1
1066	5	{1065,1067,1070,1071}	New Crea	692089085690380288	0	f	(3415,1980)	f	Salt	f	f	f	788	Lamellino	18	0	f	New Crea	692089085690380288	f	f	2
532	0	{530,531,533,600,602}	Tusail	844640695868194927	0	t	(884,2266)	t	Wood	f	f	f	3288	Korteind	23	0	f	Tusail	844640695868194927	f	f	1
1199	2	{1194,1195,1200}	Blindgulf	967635049061163028	0	t	(2349,2838)	f	Ivory	t	f	f	3925	Edestiada	0	0	f	Blindgulf	967635049061163028	t	f	2
976	2	{975,977}	Nokoroth	428949783919460363	0	t	(4122,2774)	f	Ivory	f	f	f	2966	Stamvishte	0	0	f	Nokoroth	428949783919460363	f	f	4
975	2	{973,974,976,977}	Nokoroth	428949783919460363	0	t	(4076,2736)	f	Livestock	f	f	f	2657	Kubvo	0	0	f	Nokoroth	428949783919460363	f	f	1
193	9	{192,194,196,198,199,220}	Ghad	281967961189908482	400	f	(1204,268)	f	Glass	f	f	f	189	Gorgox	0	0	f	Ghad	281967961189908482	f	f	1
1159	0	{1158,1160,1161,1162}	Blindgulf	967635049061163028	0	t	(3060,2397)	f	Paper	t	f	f	3180	Rakopan	0	0	f	Blindgulf	967635049061163028	f	f	1
160	0	{159,161,162,176,177,178}	Ghad	281967961189908482	400	f	(1444,535)	f	Sugar	f	f	f	3919	Orsier	0	0	f	Ghad	281967961189908482	t	f	2
592	2	{590,591,593,593,601,608}	Tusail	844640695868194927	0	f	(1033,2439)	f	Sugar	f	f	f	3473	Collesaro	23	0	f	Tusail	844640695868194927	f	f	1
996	0	{992,995,997,998}	New Crea	692089085690380288	414	t	(3873,1265)	f	Sugar	f	f	f	3062	Neslavgrad	13	0	f	New Crea	692089085690380288	f	f	1
81	0	{80,82,98,99,100}	Nanhai	899852149360566323	0	f	(522,796)	f	Wood	f	f	f	4153	Balloundra	0	0	f	Nanhai	899852149360566323	f	f	1
297	2	{146,147,296,298,299}	Litchmiota	637939981691912202	0	t	(1269,1006)	f	Fish	t	f	f	2583	Weststraten	15	0	f	Litchmiota	637939981691912202	t	f	2
639	9	{637,638,640}		0	160	t	(2387,79)	f	Fur	f	f	f	292	Chikutete	0	0	f		0	f	f	1
8	0	{5,6,9,33,35}		0	294	t	(936,1258)	f	Fruits	f	f	f	4508	Phade	0	0	f		0	f	f	1
336	5	{335,337,339,340,358,359}		0	1034	f	(1874,558)	f	Raw Stone	f	f	f	847	Malaotheche	0	0	f		0	f	f	2
987	1	{981,982,983,986,988}	Nokoroth	428949783919460363	0	t	(3863,2975)	f	Paper	f	f	f	631	Gabrobrod	0	0	f	Nokoroth	428949783919460363	f	f	4
497	1	{495,496}		0	0	t	(1136,1294)	f	Glass	f	f	f	554	Oudenhal	0	0	f	Sarques	353107568547201035	f	f	1
344	5	{329,330,342,343,345,346}		0	1092	f	(1861,463)	f	Coal	f	f	f	641	Viška	0	0	f		0	f	f	1
990	0	{968,989,991,1001,1002,1003}		0	270	f	(3636,1292)	f	Grain	f	f	f	3175	Traboj	0	0	f		0	f	f	2
703	2	{691,692,702,704,709,710}		0	397	f	(2819,832)	t	Livestock	f	f	f	2786	Čapčac	0	0	f		0	f	f	3
859	9	{857,858,860,861,862}	Blindgulf	0	314	t	(3715,142)	f	Glass	f	f	f	157	Toko	0	0	f		0	f	f	2
312	2	{305,310,313,314,429,430}		0	321	f	(1696,547)	f	Spices	f	f	f	2658	Dikzen	0	0	f		0	f	f	1
804	2	{759,800,803,805,809}	Correlli	293518673417732098	0	f	(3303,175)	f	Tin	f	f	f	4421	Alenlet	0	0	f	Correlli	293518673417732098	f	f	1
163	0	{161,162,164,300,483}		0	369	f	(1543,551)	t	Paper	f	f	f	4329	Nieuwschot	0	0	f		0	f	f	1
1154	5	{1124,1153,1155,1156,1169}		0	1282	f	(2941,2212)	f	Tin	f	f	f	887	Cagliana	0	0	f		0	f	f	2
32	0	{30,31,33,34,46}		0	367	f	(871,1210)	t	Fur	f	f	f	4260	Baghetonto	0	0	f		0	f	f	1
39	0	{38,40,41,42}		0	282	t	(1138,1123)	f	Livestock	f	f	f	4847	Xabuto	0	0	f		0	f	f	2
325	9	{319,320,326}		0	194	t	(1773,382)	f	Spices	f	f	f	226	Naputo	0	0	f		0	f	f	1
969	0	{965,1005,1006,1093}		0	323	t	(3364,1521)	t	Glass	f	f	f	3894	Moatida	0	0	f		0	f	f	3
348	5	{351,352}		0	1272	f	(1930,504)	f	Raw Stone	f	f	f	629	Chikulo	0	0	f		0	f	f	1
766	0	{767}		0	393	t	(3418,347)	f	Wood	f	f	f	3227	Macilacuala	0	0	f		0	f	f	1
157	0	{156,158,179,178,290,291}		0	331	f	(1372,612)	t	Cotton	f	f	f	4307	Blagoevski	0	0	f		0	f	f	2
1215	5	{698,715,1216,1217}		0	1083	f	(2741,752)	f	Gold	f	f	f	651	Svobol	0	0	f		0	f	f	1
831	5	{829,830,832,840}		0	1086	t	(3440,124)	f	Raw Stone	f	f	f	634	Martoise	0	0	f		0	f	f	3
203	9	{202,204,205}		0	186	t	(1082,292)	f	Spices	f	f	f	174	Tutravo	0	0	f		0	f	f	3
168	0	{167,168,170,172,475,476}		0	2911	f	(1487,684)	f	Wool	f	f	f	4650	Nampulimane	0	0	f		0	f	f	1
494	1	{493,495,496}		0	0	t	(1147,1352)	f	Spices	f	f	f	590	Mponlunga	0	0	f	Sarques	353107568547201035	f	f	2
379	1	{380,381,382}	Litchmiota	637939981691912202	1258	f	(1629,1075)	f	Paper	f	f	f	629	Gladenhude	2	0	f		0	f	f	3
758	2	{753,754,755,757,759,706}	Correlli	293518673417732098	0	f	(3287,245)	f	Chocolate	f	f	f	4188	Cooldong	0	0	f	Correlli	293518673417732098	f	f	3
575	7	{574,576,580,586,587}	Tusail	844640695868194927	0	f	(1006,2709)	t	Glass	f	f	f	243	Statjøen	23	0	f	Tusail	844640695868194927	f	f	1
181	2	{180,182,183,223,230}	Ghad	281967961189908482	400	f	(1339,479)	t	Wood	f	f	f	3624	Ufecad	0	0	f	Ghad	281967961189908482	t	f	2
466	1	{440,465}	Litchmiota	637939981691912202	0	t	(1908,1539)	f	Fish	f	f	f	671	Sibombwe	15	0	f	Litchmiota	637939981691912202	f	f	2
207	2	{208,212}	Ghad	281967961189908482	650	t	(1028,349)	f	Livestock	t	f	f	4361	Mursa	0	0	f	Ghad	281967961189908482	t	f	1
436	1	{435,437,464}	Litchmiota	637939981691912202	0	t	(1840,1447)	f	Fish	f	f	f	695	Goni	15	0	f	Litchmiota	637939981691912202	f	f	3
1177	0	{1175,1176,1178,1191,1192}	Blindgulf	967635049061163028	0	f	(2469,2496)	f	Fruits	f	f	f	3975	Monba	0	0	f	Blindgulf	967635049061163028	f	f	4
896	0	{888,895,897,899,900}	Blindgulf	0	4693	f	(4036,623)	f	Grain	f	f	f	3493	Faersala	0	0	f		0	f	f	1
111	2	{109,110,112,115,116}	Nanhai	899852149360566323	0	f	(679,682)	f	Precious Goods	f	f	f	3632	Petshte	0	0	f	Nanhai	899852149360566323	f	f	4
617	0	{528,603,604,616}	Tusail	844640695868194927	0	t	(713,2394)	f	Tea and Coffee	f	f	f	3582	Besanluire	23	0	f	Tusail	844640695868194927	f	f	2
474	2	{169,171,290,292,417,434,475,516}		0	376	f	(1426,736)	f	Salt	f	f	f	3590	Cinisto	0	0	f		0	f	f	1
676	0	{666,667,669,673,675,677}		0	260	f	(2905,533)	f	Sugar	f	f	f	3583	Modivia	0	0	f		0	f	f	1
633	2	{631,632}		0	385	t	(2473,349)	f	Fruits	f	f	f	4062	Marralacuala	0	0	f		0	f	f	1
954	0	{951,953,955,964,965,966}		0	311	f	(3341,1363)	f	Paper	f	f	f	3549	Xane	0	0	f		0	f	f	3
48	0	{27,30,31,46,47,49}		0	316	f	(873,1147)	f	Paper	f	f	f	3075	Mansano	0	0	f		0	f	f	3
636	2	{635,634,637,638}		0	314	t	(2396,146)	f	Salt	f	f	f	3209	Mansano	0	0	f		0	f	f	1
780	2	{779,782,783,784}	Correlli	293518673417732098	0	t	(3066,77)	f	Fruits	f	f	f	3552	Civilerno	0	0	f	Correlli	293518673417732098	f	f	2
229	2	{180,223,228,230,231,235}	Ghad	281967961189908482	400	f	(1312,540)	t	Wine	f	f	f	2733	Čedanj	0	0	f	Ghad	281967961189908482	t	f	2
505	5	{496,498,499,504,506}		0	0	f	(1201,1285)	f	Precious Stones	f	f	f	644	Nancray County	1	0	f	Sarques	353107568547201035	f	f	1
427	0	{424,426,428,430,432}		0	298	t	(1818,657)	f	Grain	f	f	f	3423	Ikhlene	0	0	f		0	f	f	4
245	0	{155,234,2346,239,244,246}		0	1123	f	(1267,650)	f	Cotton	f	f	f	4470	Guavoa	0	0	f		0	f	f	3
429	0	{310,311,312,423,428,430}		0	309	f	(1730,639)	f	Wood	f	f	f	4533	Pomolikeni	0	0	f		0	f	f	1
57	0	{23,54,56,58}		0	265	t	(601,1019)	t	Fruits	f	f	f	3921	Petva	0	0	f		0	f	f	1
69	0	{60,68,70,71}		0	264	f	(693,893)	t	Cotton	f	f	f	3829	Chaveil	0	0	f		0	f	f	4
356	2	{353,354,355,357,359}		0	380	t	(1975,580)	f	Paper	f	f	f	3639	Angousart	0	0	f		0	f	f	1
391	5	{372,390,392,418,419}		0	1134	f	(1552,819)	f	Tin	f	f	f	778	Boursier	0	0	f		0	f	f	2
428	0	{423,424,426,427,429,430}		0	292	f	(1768,648)	f	Tobacco	f	f	f	3160	Lundashi	0	0	f		0	f	f	1
396	5	{395,397,461}		0	1279	f	(1660,812)	f	Coal	f	f	f	783	Kabogwe	0	0	f		0	f	f	1
851	9	{845,846,850,852,853,854}		0	106	f	(3546,130)	f	Glass	f	f	f	185	Kawamzongwe	0	0	f		0	f	f	1
410	5	{408,409,411,412,420}		0	1165	f	(1642,778)	f	Tin	f	f	f	822	Zambewezi	0	0	f		0	f	f	3
411	5	{395,409,410,412}		0	1153	f	(1658,794)	f	Coal	f	f	f	626	Caideena	0	0	f		0	f	f	2
480	2	{165,307,478,479,481}		0	373	f	(1575,646)	f	Glass	f	f	f	3223	Bremobor	0	0	f		0	f	f	3
373	1	{372,374,375,376,451}		0	158	f	(1606,846)	f	Spices	f	f	f	794	Samorinja	0	0	f		0	f	f	1
405	5	{399,400,406,407,425}		0	1266	f	(1719,749)	f	Raw Stone	f	f	f	621	Stovar	0	0	f		0	f	f	1
1110	5	{1107,1109,1127}		0	1260	f	(3087,1922)	f	Tin	f	f	f	619	Vula	0	0	f		0	f	f	3
143	7	{142,144}		0	172	f	(1098,1030)	f	Silk	f	f	f	219	Kutivača	0	0	f		0	f	f	3
533	0	{531,532,534,598,599,600}	Tusail	844640695868194927	0	t	(940,2221)	t	Grain	f	f	f	3666	Marilet	23	0	f	Tusail	844640695868194927	f	f	2
446	0	{380,381,445,447}	Litchmiota	637939981691912202	0	t	(1620,1231)	f	Livestock	t	f	f	3437	Fagerbacka	15	0	f	Litchmiota	637939981691912202	f	f	3
275	7	{251,252,274,276,281,283}	Ghad	281967961189908482	400	f	(1078,733)	f	Silk	f	f	f	274	Talaba	0	0	f	Ghad	281967961189908482	t	f	3
516	2	{419,434,474,475,476,477}		0	2300	f	(1505,745)	t	Tin	f	f	f	3156	Großbruck	0	0	f		0	f	f	3
230	2	{180,181,223,229}	Ghad	281967961189908482	400	f	(1327,520)	t	Sugar	f	f	f	4266	Morgocaea	0	0	f	Ghad	281967961189908482	t	f	1
1192	0	{1176,1177,1191,1193}	Blindgulf	967635049061163028	0	t	(2371,2550)	f	Tobacco	t	f	f	3521	Sušiles	0	0	f	Blindgulf	967635049061163028	t	f	2
441	1	{442}	Litchmiota	637939981691912202	0	t	(1795,1523)	f	Fish	f	f	f	503	Myamine	15	0	f	Litchmiota	637939981691912202	f	f	1
209	2	{208,210,213}	Ghad	281967961189908482	400	f	(1071,360)	f	Glass	f	f	f	4460	Fandravola	0	0	f	Ghad	281967961189908482	t	f	2
607	2	{601,605,606,608,609,615}	Tusail	844640695868194927	0	f	(889,2457)	f	Copper	f	f	f	2653	Merlean	23	0	f	Tusail	844640695868194927	f	f	1
745	2	{740,742,743,746,748,749,750}	Correlli	293518673417732098	0	f	(3154,207)	f	Wood	f	f	f	3470	Manguache	0	0	f	Correlli	293518673417732098	f	f	3
371	1	{369,370,372,376,378,383}	Litchmiota	637939981691912202	0	f	(1532,911)	f	Glass	f	f	f	798	Bournoît	15	0	f	Litchmiota	637939981691912202	f	f	2
541	0	{539,542,545,547}		0	2835	t	(1462,2308)	f	Grain	f	f	f	4890	Elsterbog	8	0	f		0	f	f	1
610	1	{609,611,612,613,614}	Tusail	844640695868194927	0	f	(832,2603)	f	Spices	f	f	f	659	Tápiz	23	0	f	Tusail	844640695868194927	f	f	2
265	5	{264,289,386,415,485}		0	291	f	(1451,900)	f	Raw Stone	f	f	f	896	Krikovar	0	0	f		0	f	f	2
183	2	{177,181,182,222,223,184}	Ghad	281967961189908482	400	f	(1370,454)	t	Grain	f	f	f	3331	Sepsai	0	0	f	Ghad	281967961189908482	t	f	2
5	0	{3,4,6,8,9,10}		0	304	f	(828,1314)	f	Wool	f	f	f	3730	Lüdinghöring	0	0	f		0	f	f	4
697	5	{685,698}		0	1279	f	(2776,724)	f	Coal	f	f	f	743	Gailhude	0	0	f		0	f	f	4
478	2	{165,166,420,447,479,480}		0	351	f	(1568,677)	f	Fruits	f	f	f	3485	Eltershafen	0	0	f		0	f	f	3
419	2	{391,393,413,414,420,434,477,516}		0	396	f	(1564,738)	t	Chocolate	f	f	f	3538	Batejo	0	0	f		0	f	f	3
34	0	{31,32,33,35,36,46}		0	395	f	(958,1170)	t	Wood	f	f	f	3734	Meamoz	0	0	f		0	f	f	4
432	0	{333,335,427,431}		0	290	t	(1836,589)	f	Cotton	f	f	f	3459	Luwinwezi	0	0	f		0	f	f	2
722	0	{672,673,674,719,721,723}		0	254	f	(3105,583)	f	Tea and Coffee	f	f	f	3708	Mpila	0	0	f		0	f	f	2
693	5	{692,694,696,701,702}		0	1131	f	(2837,763)	t	Gold	f	f	f	796	Lukusama	0	0	f		0	f	f	1
646	2	{641,642,643,645,647}		0	304	t	(2594,182)	f	Rare Wood	f	f	f	2745	Kapupo	0	0	f		0	f	f	1
509	0	{508,510}		0	367	t	(520,1444)	f	Fur	f	f	f	4017	Opatilok	0	0	f		0	f	f	1
414	5	{393,394,413,419}		0	1207	f	(1606,794)	f	Salt	f	f	f	786	Križepina	0	0	f		0	f	f	1
417	2	{292,415,416,434,474}		0	317	f	(1417,774)	t	Ivory	f	f	f	3985	Dubropin	0	0	f		0	f	f	1
14	0	{13,15}		0	279	t	(610,1278)	f	Livestock	f	f	f	3531	Bjegrad	0	0	f		0	f	f	2
49	0	{27,47,48,50,51,52,53}		0	260	f	(835,1100)	t	Precious Goods	f	f	f	4357	Cuxkamp	0	0	f		0	f	f	4
406	2	{405,407,421,422,425}		0	302	f	(1674,720)	t	Livestock	f	f	f	2682	Vibos	0	0	f		0	f	f	1
90	2	{87,88,89,91}		0	323	t	(347,844)	f	Tea and Coffee	f	f	f	3651	Gafarosa	0	0	f		0	f	f	1
504	5	{500,505,506}		0	1278	f	(1222,1298)	f	Copper	f	f	f	601	Lupagani	0	0	f		0	f	f	4
422	2	{309,311,406,421,423,425}		0	375	f	(1685,695)	t	Spices	f	f	f	3987	Mazoru	0	0	f		0	f	f	3
656	2	{654,655,657,658}		0	322	t	(2749,117)	f	Ivory	f	f	f	3767	Buton	0	0	f		0	f	f	1
683	2	{681,682,684,716,717}		0	388	f	(2586,593)	f	Tea and Coffee	f	f	f	3130	Gwani	0	0	f		0	f	f	4
273	2	{268,269,272,274,287,289}		0	308	f	(992,844)	f	Ivory	f	f	f	3336	Raffirowa	0	0	f		0	f	f	2
508	0	{507,509}		0	351	t	(643,1444)	f	Cotton	f	f	f	3621	Chakage	0	0	f		0	f	f	1
7	0	{4,6}		0	376	t	(938,1377)	f	Fish	f	f	f	4182	Turbawa	0	0	f		0	f	f	1
534	0	{533,535,598}	Tusail	844640695868194927	0	t	(1001,2196)	f	Grain	f	f	f	4067	Donoch	23	0	f	Tusail	844640695868194927	f	f	1
738	2	{732,733,737,739,746,747}	Correlli	293518673417732098	0	t	(3172,328)	f	Salt	f	f	f	3367	Mitief	0	0	f	Correlli	293518673417732098	f	f	1
785	2	{784,786}	Correlli	293518673417732098	0	t	(3136,27)	f	Salt	f	f	f	2643	Ávirón	0	0	f	Correlli	293518673417732098	f	f	1
774	2	{773,775,777,778}	Correlli	293518673417732098	0	t	(2959,134)	f	Paper	f	f	f	3065	Clonakee	0	0	f	Correlli	293518673417732098	f	f	2
205	9	{203,204,206}		0	128	t	(1053,308)	f	Glass	f	f	f	237	Romroda	0	0	f		0	f	f	2
370	1	{289,369,371,372,288,289,463}	Litchmiota	637939981691912202	0	f	(1467,904)	f	Glass	f	f	f	566	Esmoxa	15	0	f	Litchmiota	637939981691912202	f	f	1
234	2	{155,231,233,235,236,237,245}	Ghad	281967961189908482	400	f	(1244,587)	f	Fruits	f	f	f	4063	Yusquile	0	0	f	Ghad	281967961189908482	t	f	1
127	2	{113,126,128,129}	Nanhai	899852149360566323	0	f	(814,745)	t	Tobacco	f	f	f	2726	Granderry	0	0	f	Nanhai	899852149360566323	f	f	4
521	2	{518,520,522,524}	Tusail	844640695868194927	0	t	(389,2041)	f	Tobacco	f	f	f	3944	Nereicada	23	0	f	Tusail	844640695868194927	f	f	2
206	9	{205}		0	251	t	(1039,326)	f	Fish	f	f	f	206	Manlang	0	0	f		0	f	f	3
1189	2	{1186,1188,1190,1196,1197,1198}	Blindgulf	967635049061163028	0	f	(2860,2655)	f	Copper	f	f	f	2900	Seria	0	0	f	Blindgulf	967635049061163028	f	f	1
475	2	{168,169,474,476,516}		0	2254	f	(1485,729)	f	Copper	f	f	f	3163	Galirez	0	0	f		0	f	f	4
600	0	{532,533,593,599,601,602}	Tusail	844640695868194927	0	f	(954,2315)	t	Tea and Coffee	f	f	f	4176	Ålerum	23	0	f	Tusail	844640695868194927	f	f	2
750	2	{743,745,749,751,752}	Correlli	293518673417732098	0	t	(3186,148)	f	Paper	f	f	f	3491	Kampagazi	0	0	f	Correlli	293518673417732098	f	f	2
227	2	{224,225,226,228,233,232}	Ghad	281967961189908482	400	f	(1210,520)	f	Wood	f	f	f	3543	Ceras	0	0	f	Ghad	281967961189908482	f	f	1
484	2	{259,266,298,299,368,369}	Litchmiota	637939981691912202	0	f	(1352,992)	f	Livestock	f	f	f	3318	Maabwe	15	0	f	Litchmiota	637939981691912202	t	f	1
26	0	{24,25,27,29,30}		0	347	f	(792,1145)	f	Fur	f	f	f	4627	Vevto	0	0	f		0	f	f	2
1006	0	{969,1004,1005,1007,1008}		0	252	t	(3427,1526)	t	Paper	f	f	f	4043	Skoplesta	0	0	f		0	f	f	1
655	2	{652,653,654,656}		0	310	t	(2711,92)	f	Fur	f	f	f	4199	Bikov	0	0	f		0	f	f	3
338	5	{337,339,342,350}		0	1042	f	(1872,526)	f	Coal	f	f	f	647	Clonkilty	0	0	f		0	f	f	3
871	9	{865,866,867,868,870,872,873}	Blindgulf	0	301	f	(3910,157)	f	Fur	f	f	f	263	Iličani	0	0	f		0	f	f	2
96	0	{71,95,97,102,105,107}		0	319	f	(670,846)	f	Wood	f	f	f	3168	Dunford	0	0	f		0	f	f	2
951	0	{949,950,952,953,955}		0	366	f	(3319,1303)	f	Wood	f	f	f	3732	Cavila	0	0	f		0	f	f	2
716	2	{683,684,714,715,717}		0	311	f	(2626,657)	f	Wood	f	f	f	3807	Penhati	0	0	f		0	f	f	1
1095	0	{960,1088,1094,1096,1101,1102}		0	370	f	(3038,1638)	f	Wood	f	f	f	4374	Gopanzi	0	0	f		0	f	f	2
1217	5	{702,712,715,1215,1216}		0	1187	f	(2734,792)	f	Iron	f	f	f	819	Shamdu	0	0	f		0	f	f	2
1073	7	{1063,1072,1074,1075}		0	152	t	(3351,1766)	t	Coal	f	f	f	265	Marondera	0	0	f		0	f	f	3
949	0	{948,950,951,955,956}		0	270	t	(3244,1316)	f	Tobacco	f	f	f	4985	Gooneragan	0	0	f		0	f	f	2
141	7	{140,142,144,268,269,270}		0	111	f	(1021,999)	f	Silk	f	f	f	245	Dojrovo	0	0	f		0	f	f	1
706	0	{691,704,705,708,707}		0	376	t	(2923,956)	f	Grain	f	f	f	4140	Poja	0	0	f		0	f	f	1
140	7	{44,139,141,142,270}		0	151	f	(1001,1006)	f	Coal	f	f	f	153	Zabar	0	0	f		0	f	f	1
637	9	{634,636,638,639,640}		0	155	t	(2425,124)	f	Fur	f	f	f	270	Velša	0	0	f		0	f	f	2
330	9	{328,329,331,344,345}		0	181	t	(1876,421)	f	Fish	f	f	f	222	Macgar	0	0	f		0	f	f	1
677	2	{666,675,676,678,687,688}		0	380	f	(2862,557)	f	Iron	f	f	f	3631	Maccommon	0	0	f		0	f	f	2
139	7	{44,137,138,140,270}		0	137	f	(952,970)	f	Paper	f	f	f	224	Shanway	0	0	f		0	f	f	2
672	0	{669,671,673,722,723,724}		0	370	f	(3045,569)	f	Grain	f	f	f	4828	Castlegheda	0	0	f		0	f	f	2
1014	0	{998,999,1013,1015}		0	276	t	(3927,1379)	f	Cotton	f	f	f	3050	Naran	0	0	f		0	f	f	1
352	2	{340,348,351,353,359}		0	343	f	(1924,520)	f	Wood	f	f	f	2810	Doroteşti	0	0	f		0	f	f	2
1135	0	{940,1133,1134,1136,1140,1141}	Khokand	905858887926816768	0	f	(2680,1589)	t	Wool	f	f	f	4102	Opthal	18	0	f	Khokand	905858887926816768	f	f	3
624	1	{625}	Litchmiota	637939981691912202	0	t	(2027,1600)	f	Glass	f	f	f	795	Opnacht	15	0	f	Litchmiota	637939981691912202	f	f	2
1033	0	{1012,1028,1032,1031,1034,1036,1037}		0	1383	f	(3852,1530)	t	Spices	f	f	f	4344	Konica	36	0	f		0	f	f	2
825	5	{819,823,824}		0	445	f	(3420,139)	f	Coal	f	f	f	777	Allankal	15	0	f		0	f	f	1
186	9	{185,187,195,221}	Ghad	281967961189908482	650	t	(1300,367)	f	Glass	t	f	f	164	Cirebau	0	0	f	Ghad	281967961189908482	f	f	4
1139	0	{1136,1137,1138,1140,1149,1150,1151}	Khokand	905858887926816768	0	f	(2577,1582)	f	Tobacco	f	f	f	3327	Kreuzstein	18	0	f	Khokand	905858887926816768	f	f	3
535	0	{534,536,596,597,598}	Tusail	844640695868194927	0	t	(1046,2169)	f	Tobacco	f	f	f	3253	Chimanira	23	0	f	Tusail	844640695868194927	f	f	2
254	2	{249,253,255,256}	Litchmiota	637939981691912202	0	f	(1163,931)	t	Fur	f	f	f	3547	Panzar	15	0	f	Litchmiota	637939981691912202	t	f	3
965	0	{954,964,966,1005,1092,1093}		0	265	f	(3328,1461)	f	Precious Goods	f	f	f	3755	Târrest	0	0	f		0	f	f	2
390	5	{370,372,389,391,418,485}		0	1233	f	(1537,835)	f	Salt	f	f	f	869	Piterşa	0	0	f		0	f	f	1
846	9	{842,843,844,845,847,850,851}		0	152	f	(3513,150)	f	Glass	f	f	f	222	Conmon	0	0	f		0	f	f	1
136	7	{50,51,133,134,135,137,138}		0	135	f	(880,976)	f	Paper	f	f	f	281	Amersdaal	0	0	f		0	f	f	1
840	5	{831,832,839,841}		0	1043	t	(3469,115)	f	Silver	f	f	f	688	Zoetermegen	0	0	f		0	f	f	4
1117	5	{1081,1112,1116,1118}		0	1160	f	(3168,2046)	f	Gold	f	f	f	647	Devenberg	0	0	f		0	f	f	2
1115	5	{1112,1113,1114,1116,1120,1123,1126}		0	1047	f	(3065,2037)	f	Coal	f	f	f	738	Dierburg	0	0	f		0	f	f	2
60	0	{55,56,59,61,67,68,69,70}		0	393	f	(686,947)	t	Wood	f	f	f	3288	Blokstadt	0	0	f		0	f	f	3
913	0	{904,911,912,914,916,917,918}	Blindgulf	0	7434	f	(3807,612)	t	Grain	f	f	f	3717	Slolo	0	0	f		0	f	f	2
35	0	{8,33,34,36}		0	390	t	(1024,1210)	f	Wool	f	f	f	3655	Zamovia	0	0	f		0	f	f	1
337	5	{336,338,339}		0	1235	f	(1858,542)	f	Copper	f	f	f	600	Valejón	0	0	f		0	f	f	1
1044	2	{1009,1035,1043,1045,1046,1047}		0	370	f	(3569,1634)	t	Tea and Coffee	f	f	f	4387	Zastela	0	0	f		0	f	f	4
331	9	{330,345,347,351}		0	102	t	(1917,434)	f	Spices	f	f	f	182	Balgăşani	0	0	f		0	f	f	2
262	5	{260,261,266,289,294}		0	1251	f	(1384,916)	f	Coal	f	f	f	730	Panteghetu	0	0	f		0	f	f	1
1091	0	{961,962,963,1090,1092}		0	356	f	(3216,1497)	f	Grain	f	f	f	4821	Bârftea	0	0	f		0	f	f	1
23	0	{22,24,25,53,54,56,57}		0	316	t	(675,1064)	f	Grain	f	f	f	3407	Timirad	0	0	f		0	f	f	1
156	0	{154,155,157,179,291}		0	322	f	(1348,664)	t	Wood	f	f	f	4115	Fetegalia	0	0	f		0	f	f	4
1036	0	{1033,1034,1035,1037,1043}		0	285	f	(3740,1587)	f	Glass	f	f	f	3345	Slojud	0	0	f		0	f	f	1
3	0	{1,2,4,5,10,11}		0	313	t	(812,1332)	t	Fruits	f	f	f	4409	Waaloord	0	0	f		0	f	f	2
838	5	{837,839,842,843}		0	1215	f	(3474,159)	f	Coal	f	f	f	864	Amerskerk	0	0	f		0	f	f	1
403	5	{401,402,425,426}		0	1083	f	(1784,715)	f	Salt	f	f	f	637	Ashuizen	0	0	f		0	f	f	1
107	2	{96,97,105,106,108}		0	386	t	(715,805)	t	Wine	f	f	f	4098	Amstelstadt	0	0	f		0	f	f	2
1088	7	{1087,1089,1094,1095,1102,1103}		0	148	f	(3074,1672)	t	Rare Wood	f	f	f	270	Emmelzaal	0	0	f		0	f	f	1
565	7	{562,564,566,569,570}		0	138	f	(1249,2743)	f	Coal	f	f	f	237	Knjazamane	0	0	f		0	f	f	1
696	5	{685,686,687,693,694,695}		0	1185	f	(2799,695)	f	Tin	f	f	f	718	Stanirig	0	0	f		0	f	f	1
137	7	{133,136,138,139,270,271,288}		0	116	f	(927,927)	f	Glass	f	f	f	290	Arankinda	0	0	f		0	f	f	1
31	0	{30,32,33,34,46,48}		0	374	f	(889,1177)	t	Tea and Coffee	f	f	f	3883	Šavor	0	0	f		0	f	f	2
86	5	{78,79,85,87,93}		0	1119	f	(405,832)	f	Copper	f	f	f	682	Granovci	0	0	f		0	f	f	2
30	0	{26,27,29,31,32,48}		0	336	f	(848,1174)	t	Wool	f	f	f	3461	Laustätten	0	0	f		0	f	f	2
691	2	{689,690,692,703,704,706,707}		0	393	f	(2898,794)	f	Spices	f	f	f	3898	Wädensberg	0	0	f		0	f	f	3
55	0	{54,56,59,60,61}		0	361	f	(704,997)	t	Spices	f	f	f	3940	Freienbach	0	0	f		0	f	f	2
1037	2	{1026,1027,1028,1033,1036,1038,1042,1043}		0	321	f	(3774,1663)	t	Fruits	f	f	f	3680	Kragudište	0	0	f		0	f	f	1
1067	7	{1065,1066,1068,1069,1080}	New Crea	692089085690380288	3081	t	(3375,2034)	f	Silk	f	f	f	287	Vesterkilde	0	0	f	New Crea	692089085690380288	f	f	3
529	0	{527,528,530,602,603}	Tusail	844640695868194927	0	f	(756,2297)	t	Sugar	f	f	f	3052	Spojba	23	0	f	Tusail	844640695868194927	f	f	2
930	0	{928,929,931}	Khokand	905858887926816768	0	t	(2860,1291)	t	Sugar	f	f	f	3108	Rogaje	18	0	f	Khokand	905858887926816768	f	f	2
1084	5	{1076,1077,1078,1083,1085}	New Crea	692089085690380288	179	f	(3231,1893)	f	Gold	f	f	f	774	Ostermance	16	0	f	New Crea	692089085690380288	f	f	4
777	2	{774,775,776,778,779}	Correlli	293518673417732098	0	f	(2997,127)	f	Tobacco	f	f	f	4405	Laufenkon	0	0	f	Correlli	293518673417732098	f	f	2
820	5	{813,816,819,821,824}	Correlli	293518673417732098	0	f	(3393,144)	f	Salt	f	f	f	649	Lojašeišta	0	0	f	Correlli	293518673417732098	f	f	4
580	7	{575,576,579,581,585,586}	Tusail	844640695868194927	0	f	(961,2738)	t	Coal	f	f	f	274	Skjoldbæk	23	0	f	Tusail	844640695868194927	f	f	1
1188	2	{1186,1187,1189,1198,1202,1204}	Blindgulf	967635049061163028	0	f	(2862,2770)	f	Glass	f	f	f	3623	Aquasa	0	0	f	Blindgulf	967635049061163028	t	f	1
116	2	{110,111,115,117,118}	Nanhai	899852149360566323	0	t	(652,650)	f	Livestock	f	f	f	3409	Novac	0	0	f	Nanhai	899852149360566323	f	f	2
1152	0	{1146,1147,1148,1151}	Khokand	905858887926816768	0	t	(2484,1731)	f	Wood	f	f	f	4230	Murskem	18	0	f	Khokand	905858887926816768	f	f	1
606	2	{604,605,607,615,616}	Tusail	844640695868194927	0	f	(832,2475)	f	Spices	f	f	f	4379	Oshammer	23	0	f	Tusail	844640695868194927	f	f	1
743	2	{742,745,750}	Correlli	293518673417732098	0	t	(3121,173)	f	Tobacco	f	f	f	3320	Bulle	0	0	f	Correlli	293518673417732098	f	f	1
1008	0	{1002,1006,1007,1009,1045}	New Crea	692089085690380288	67	t	(3546,1506)	t	Paper	f	f	f	4488	Noše	17	0	f	New Crea	692089085690380288	t	f	2
1053	2	{1050,1052,1054,1055,1056,1057}	Nokoroth	428949783919460363	0	f	(3666,1996)	f	Livestock	f	f	f	2885	Jagogaška	0	0	f	Nokoroth	428949783919460363	f	f	1
1147	0	{1142,1144,1145,1146,1148,1149,1150,1152}	Khokand	905858887926816768	0	f	(2590,1740)	f	Grain	f	f	f	4945	Vejlev	18	0	f	Khokand	905858887926816768	f	f	2
1203	2	{1202,1204,1205}	Blindgulf	967635049061163028	0	t	(2831,3020)	f	Wood	t	f	f	3331	Gänsernkirchen	0	0	f	Blindgulf	967635049061163028	t	f	1
192	9	{189,191,193,196}	Ghad	281967961189908482	650	t	(1269,238)	f	Precious Goods	t	f	f	209	Orastro	0	0	f	Ghad	281967961189908482	t	f	1
367	0	{365,366,368}	Litchmiota	637939981691912202	0	t	(1395,1096)	f	Tobacco	t	f	f	3099	Dillenwig	15	0	f	Litchmiota	637939981691912202	f	f	1
641	9	{642,646}		0	173	t	(2560,175)	f	Fur	f	f	f	267	Aramane	0	0	f		0	f	f	1
423	0	{311,422,424,425,428,429}		0	377	f	(1739,661)	t	Ivory	f	f	f	4513	Kraguvac	0	0	f		0	f	f	2
82	0	{80,81,83,84,100,101}	Nanhai	899852149360566323	0	f	(495,790)	f	Rare Wood	f	f	f	4948	Panrig	0	0	f	Nanhai	899852149360566323	f	f	1
77	2	{76,78,93}		0	369	t	(400,954)	f	Tin	f	f	f	3209	Reilach	0	0	f		0	f	f	2
483	0	{163,164,300,481,482}		0	359	f	(1577,551)	f	Grain	f	f	f	4396	Herneuve	0	0	f		0	f	f	1
515	2	{513,514}		0	340	t	(488,1012)	f	Tea and Coffee	f	f	f	3806	Menbon	0	0	f		0	f	f	3
164	0	{161,163,165,167,173,481,483}		0	355	f	(1512,603)	t	Cotton	f	f	f	4025	Konice	0	0	f		0	f	f	3
967	0	{952,953,966,968,1003,1004}		0	263	t	(3513,1336)	t	Tobacco	f	f	f	4331	Dravovica	0	0	f		0	f	f	2
663	0	{661,662,664,667,668}		0	385	t	(2871,403)	f	Wool	f	f	f	4937	Črnolavž	0	0	f		0	f	f	3
1034	0	{1010,1012,1033,1035,1036}		0	390	f	(3758,1519)	f	Glass	f	f	f	4622	Jerice	0	0	f		0	f	f	2
1035	0	{1009,1010,1034,1036,1043,1044}		0	309	f	(3670,1555)	f	Fur	f	f	f	3964	Škofkem	0	0	f		0	f	f	1
849	9	{847,848,850,853}		0	171	t	(3521,88)	f	Fur	f	f	f	250	Mujana	0	0	f		0	f	f	3
647	2	{645,646,648}		0	347	t	(2657,216)	f	Fish	f	f	f	3358	Ratina	0	0	f		0	f	f	3
875	2	{863,864,874,876,877}	Blindgulf	0	6536	t	(3703,340)	f	Grain	f	f	f	3268	Smedestrup	0	0	f		0	f	f	1
659	0	{660,661}		0	381	t	(2833,301)	f	Fish	f	f	f	4548	Guldhus	0	0	f		0	f	f	2
59	0	{55,56,58,60,70}		0	257	f	(637,965)	f	Sugar	f	f	f	3141	Dybborg	0	0	f		0	f	f	3
839	5	{838,840,841,842,847}		0	1199	f	(3472,128)	f	Coal	f	f	f	848	Vestergård	0	0	f		0	f	f	2
507	0	{508}		0	361	t	(706,1433)	f	Grain	f	f	f	4442	Vindholt	0	0	f		0	f	f	2
17	0	{15,16,18,21}		0	321	t	(621,1188)	f	Ivory	f	f	f	4215	Kirkehus	0	0	f		0	f	f	2
306	0	{303,304,305,307,308,309,310}		0	270	f	(1649,596)	f	Rare Wood	f	f	f	3756	Pizhany	0	0	f		0	f	f	1
1010	0	{1001,1002,1009,1011,1012,1034,1035}	New Crea	692089085690380288	702	f	(3645,1476)	f	Tobacco	f	f	f	3876	Asren	10	0	f	New Crea	692089085690380288	f	f	2
1075	5	{1070,1072,1073,1074,1076,1077}	New Crea	692089085690380288	432	f	(3328,1859)	f	Copper	f	f	f	803	Kobíč	13	0	f	New Crea	692089085690380288	f	f	3
240	2	{238,239,241,242,243,244}		0	2626	f	(1192,706)	f	Livestock	f	f	f	4321	Tubbokaye	0	0	f		0	f	f	3
1099	0	{1096,1097,1098,1100,1130}	Khokand	905858887926816768	0	f	(2883,1611)	t	Spices	f	f	f	3423	Těkolov	18	0	f	Khokand	905858887926816768	f	f	2
736	2	{734,735,737,739,741}	Correlli	293518673417732098	0	f	(3067,299)	f	Fur	f	f	f	3099	Guarcia	0	0	f	Correlli	293518673417732098	f	f	2
103	2	{102,104,105,109,110}	Nanhai	899852149360566323	0	f	(623,727)	f	Paper	f	f	f	4089	Bjørnbæk	0	0	f	Nanhai	899852149360566323	f	f	1
110	2	{103,104,111,116}	Nanhai	899852149360566323	0	t	(614,700)	f	Copper	f	f	f	2958	Otesuu	0	0	f	Nanhai	899852149360566323	f	f	2
105	2	{97,102,103,106,107}	Nanhai	899852149360566323	0	f	(652,776)	t	Copper	f	f	f	4396	Narme	0	0	f	Nanhai	899852149360566323	f	f	2
942	0	{932,933,940,941,943,1097,1098}	Khokand	905858887926816768	0	f	(2848,1474)	t	Glass	f	f	f	3507	Rødkilde	18	0	f	Khokand	905858887926816768	f	f	4
382	1	{378,379,381,383,384,385}	Litchmiota	637939981691912202	0	f	(1550,1060)	f	Ivory	f	f	f	762	Dublee	15	0	f	Litchmiota	637939981691912202	f	f	2
821	5	{812,813,820,822,823,824}		0	317	f	(3391,124)	f	Silver	f	f	f	722	Kongehus	15	0	f		0	f	f	2
101	0	{82,83,100}	Nanhai	899852149360566323	0	t	(508,729)	f	Grain	f	f	f	3289	Räru	0	0	f	Nanhai	899852149360566323	f	f	1
1160	0	{1159,1161,1182,1183}	Blindgulf	967635049061163028	0	t	(3121,2446)	f	Sugar	t	f	f	3495	Strandstrup	0	0	f	Blindgulf	967635049061163028	f	f	3
473	1	{469,487,488}	Litchmiota	637939981691912202	0	t	(1298,1318)	f	Paper	f	f	f	791	Cernarşa	15	0	f	Litchmiota	637939981691912202	f	f	1
678	2	{665,666,677,680,684,686,687}		0	301	f	(2779,573)	f	Iron	f	f	f	4143	Birkestrup	0	0	f		0	f	f	2
852	9	{845,851,854,856}		0	195	t	(3575,162)	f	Fish	f	f	f	196	Enshus	0	0	f		0	f	f	1
715	2	{684,685,698,712,714,716,1215,1217}		0	302	f	(2680,686)	f	Salt	f	f	f	3765	Lillerup	0	0	f		0	f	f	3
154	0	{152,153,155,156,246,291,292}		0	306	f	(1291,700)	t	Grain	f	f	f	4445	Møllerup	0	0	f		0	f	f	2
1071	5	{1063,1065,1066,1070,1072}	New Crea	692089085690380288	69	f	(3416,1906)	f	Iron	f	f	f	780	Scythe	17	0	f	New Crea	692089085690380288	f	f	4
144	0	{141,142,143,145,256,267,268}		0	321	t	(1089,983)	f	Livestock	f	f	f	4642	Guldskov	0	0	f		0	f	f	3
248	0	{149,150,151,153,246,247}		0	318	f	(1251,839)	f	Livestock	f	f	f	4075	Silkeholt	0	0	f		0	f	f	3
812	2	{811,813,821,822}	Correlli	293518673417732098	0	t	(3325,99)	f	Fur	f	f	f	2972	Riorez	0	0	f	Correlli	293518673417732098	f	f	2
56	0	{54,55,57,58,59,60}		0	335	f	(664,1001)	f	Tea and Coffee	f	f	f	3358	Skitrykaw	0	0	f		0	f	f	1
64	0	{52,63,66,134,135}		0	263	f	(828,952)	t	Paper	f	f	f	3072	Shchusna	0	0	f		0	f	f	1
1092	0	{963,964,965,1090,1091,1093}		0	276	f	(3276,1499)	f	Wool	f	f	f	3364	Narostavy	0	0	f		0	f	f	3
593	2	{591,592,594,599,600,601}	Tusail	844640695868194927	0	f	(1028,2374)	f	Paper	f	f	f	3899	Vitsyezyr	23	0	f	Tusail	844640695868194927	f	f	2
1141	0	{1133,1135,1140,1142,1149}	Khokand	905858887926816768	0	f	(2682,1647)	t	Precious Goods	f	f	f	3648	Kiviõsalu	18	0	f	Khokand	905858887926816768	f	f	2
279	7	{277,280,433}	Ghad	281967961189908482	650	t	(1015,589)	t	Glass	f	f	f	264	Bebiu	0	0	f	Ghad	281967961189908482	f	f	2
674	0	{673,675,719,722}		0	383	t	(3051,668)	f	Wood	f	f	f	4982	Kaldi	0	0	f		0	f	f	1
904	0	{892,893,902,903,905,906,911,913,918}	Blindgulf	0	6329	f	(3823,517)	t	Cotton	f	f	f	4837	Tajandi	0	0	f		0	f	f	3
687	2	{677,678,688,686,694,695,696}		0	308	f	(2788,638)	f	Glass	f	f	f	3898	Kargeva	0	0	f		0	f	f	2
662	0	{659,660,661,663}		0	373	t	(2869,358)	f	Cotton	f	f	f	3862	Litště	0	0	f		0	f	f	2
640	9	{637,638,639}		0	157	t	(2452,99)	f	Fur	f	f	f	282	Valapa	0	0	f		0	f	f	1
762	0	{0}		0	298	t	(3575,261)	f	Sugar	f	f	f	3983	Palde	0	0	f		0	f	f	1
346	5	{342,344,345,347,349,350}		0	1062	f	(1894,490)	f	Tin	f	f	f	784	Sinsa	0	0	f		0	f	f	1
288	2	{132,133,137,271,286}		0	353	f	(934,871)	t	Ivory	f	f	f	3038	Räpila	0	0	f		0	f	f	1
650	9	{649,651,652}		0	137	t	(2592,74)	f	Glass	f	f	f	177	Karski	0	0	f		0	f	f	2
564	7	{562,563,565,566}		0	119	t	(1300,2749)	f	Fish	f	f	f	231	Karngi	0	0	f		0	f	f	2
847	9	{839,841,842,846,848,849,850}		0	104	f	(3501,110)	f	Fur	f	f	f	208	Kurepää	0	0	f		0	f	f	3
850	9	{846,847,849,851,853}		0	104	f	(3528,119)	f	Glass	f	f	f	217	Rapli	0	0	f		0	f	f	4
1070	5	{1066,1071,1072,1075,1077,1078,1079}	New Crea	692089085690380288	137	f	(3335,1926)	f	Tin	f	f	f	866	Asdaal	16	0	f	New Crea	692089085690380288	f	f	1
1064	2	{1061,1062,1063,1065}	New Crea	692089085690380288	0	f	(3488,1859)	f	Tobacco	f	f	f	2932	Keflajahlíð	18	0	f	New Crea	692089085690380288	f	f	2
211	2	{200,201,202,210}		0	2278	f	(1120,326)	f	Glass	f	f	f	2552	Quecos	0	0	f		0	f	f	1
1000	0	{991,997,998,999,1001,1011}	New Crea	692089085690380288	0	f	(3724,1337)	f	Grain	f	f	f	4303	Vsebram	18	0	f	New Crea	692089085690380288	f	f	1
386	1	{362,363,364,385,387,445}	Litchmiota	637939981691912202	0	f	(1458,1224)	f	Glass	f	f	f	717	Skogby	15	0	f	Litchmiota	637939981691912202	f	f	1
525	2	{522,524,526}	Tusail	844640695868194927	0	t	(405,2169)	f	Fish	t	f	f	4370	Keusämäki	23	0	f	Tusail	844640695868194927	f	f	3
824	5	{819,820,821,823,825}		0	333	f	(3402,135)	f	Precious Stones	f	f	f	706	Niniemi	15	0	f		0	f	f	1
741	2	{735,736,739,740,742}	Correlli	293518673417732098	0	t	(3046,245)	f	Copper	f	f	f	4394	Heissa	0	0	f	Correlli	293518673417732098	f	f	1
723	0	{672,721,722,724,725}	Correlli	293518673417732098	27169	t	(3134,558)	f	Ivory	f	f	f	3515	Raaseko	0	0	f	Correlli	293518673417732098	f	f	4
752	2	{749,750,751,753,759,800}	Correlli	293518673417732098	0	f	(3231,173)	f	Tea and Coffee	f	f	f	4448	Belvor	0	0	f	Correlli	293518673417732098	f	f	3
239	2	{236,237,238,240,244,245}		0	1356	f	(1222,686)	f	Fruits	f	f	f	2665	Kiviõtu	0	0	f		0	f	f	1
219	2	{199,217,218,220,221,225}	Ghad	281967961189908482	400	f	(1186,403)	t	Salt	f	f	f	4490	Osterlein	0	0	f	Ghad	281967961189908482	t	f	1
1002	0	{990,1001,1003,1007,1008,1009,1010}	New Crea	692089085690380288	41	f	(3582,1409)	f	Fur	f	f	f	3196	Riihivalta	17	0	f	New Crea	692089085690380288	f	f	1
808	2	{807,809,815,816}	Correlli	293518673417732098	0	t	(3359,191)	f	Salt	f	f	f	4498	Dudok	0	0	f	Correlli	293518673417732098	f	f	1
1057	2	{1053,1056,1058,1059}	Nokoroth	428949783919460363	0	t	(3600,2066)	f	Sugar	f	f	f	4443	Kiskunta	0	0	f	Nokoroth	428949783919460363	f	f	1
465	1	{439,440,466}	Litchmiota	637939981691912202	0	t	(2106,1503)	f	Precious Stones	f	f	f	783	Oxelögrund	15	0	f	Litchmiota	637939981691912202	f	f	3
175	5	{158,159,172,173,174}	Ghad	281967961189908482	400	f	(1465,630)	f	Silver	f	f	f	606	Steffisborn	0	0	f	Ghad	281967961189908482	f	f	1
531	0	{530,532,533}	Tusail	844640695868194927	0	t	(832,2225)	f	Glass	f	f	f	4409	Ylöpula	23	0	f	Tusail	844640695868194927	f	f	1
43	0	{37,41,42,44,45}	"Soupy Zuzek"	552224320257130496	995	f	(1039,1091)	f	Grain	f	f	f	4690	Szenbóvár	8	0	f	"Soupy Zuzek"	552224320257130496	f	f	3
311	0	{309,310,422,423,429}		0	376	f	(1699,655)	f	Rare Wood	f	f	f	4181	Hrakov	0	0	f		0	f	f	1
1127	7	{1101,1109,1110,1113,1114,1126}	New Crea	692089085690380288	157	t	(2914,1863)	t	Silk	f	f	f	240	Haniemi	16	0	f	New Crea	692089085690380288	f	f	2
359	2	{336,340,352,353,356,357}		0	336	f	(1908,567)	f	Tobacco	f	f	f	3899	Chomusou	0	0	f		0	f	f	2
399	5	{397,398,400,405,407}		0	1097	f	(1719,763)	f	Spices	f	f	f	665	Mänranta	0	0	f		0	f	f	1
542	0	{541,543,545}		0	2230	t	(1559,2315)	f	Fur	f	f	f	3280	Pietarni	9	0	f		0	f	f	1
45	0	{37,43,44,46,47}		0	301	f	(974,1096)	t	Tobacco	f	f	f	3190	Kuripunki	0	0	f		0	f	f	4
870	9	{868,869,871,872,880}	Blindgulf	0	291	f	(3985,171)	f	Spices	f	f	f	251	Juanttinen	0	0	f		0	f	f	3
699	5	{698,700,1216}		0	1243	f	(2779,738)	f	Precious Stones	f	f	f	669	Kitali	0	0	f		0	f	f	2
249	2	{149,247,250,253,254,255}		0	363	f	(1181,900)	t	Tea and Coffee	f	f	f	2993	Töson	0	0	f		0	f	f	3
714	2	{712,713,715,716,717}		0	342	t	(2605,724)	f	Wood	f	f	f	3761	Szartak	0	0	f		0	f	f	1
334	2	{323,329,333,335,343}		0	310	f	(1820,466)	f	Wood	f	f	f	4424	Lajojosmizse	0	0	f		0	f	f	3
318	9	{316,317,319}		0	109	t	(1703,378)	f	Ivory	f	f	f	239	Orimamäki	0	0	f		0	f	f	3
669	0	{667,668,670,671,672,673,676}		0	346	f	(2979,493)	f	Wood	f	f	f	3821	Nosiä	0	0	f		0	f	f	2
995	0	{992,994,996}	Blindgulf	0	6876	t	(3857,1208)	f	Tobacco	f	f	f	3438	Raittinen	0	0	f		0	f	f	1
826	5	{817,827,828}		0	1024	f	(3420,169)	f	Salt	f	f	f	737	Kanttila	0	0	f		0	f	f	4
76	2	{74,75,77,78,79}		0	336	t	(472,936)	f	Precious Goods	f	f	f	4371	Keszna	0	0	f		0	f	f	1
688	2	{675,677,687,689,694}		0	307	f	(2889,659)	f	Chocolate	f	f	f	4232	Mosfellssós	0	0	f		0	f	f	1
13	0	{11,12,14,15,16,19}		0	390	t	(670,1276)	f	Grain	f	f	f	3131	Reykvöllur	0	0	f		0	f	f	4
704	0	{691,703,705,706,709}		0	267	t	(2801,936)	f	Paper	f	f	f	4591	Grundarsker	0	0	f		0	f	f	1
1001	0	{990,991,1000,1002,1010,1011}	New Crea	692089085690380288	30	f	(3643,1355)	f	Livestock	f	f	f	4296	Hvanseyri	17	0	f	New Crea	692089085690380288	f	f	1
528	0	{527,529,603,617}	Tusail	844640695868194927	0	t	(700,2340)	f	Wood	f	f	f	4561	Rîșcați	23	0	f	Tusail	844640695868194927	f	f	3
615	1	{606,607,614,616,619}	Tusail	844640695868194927	0	f	(797,2518)	f	Glass	f	f	f	696	Salactene	23	0	f	Tusail	844640695868194927	f	f	4
443	0	{360,361,444}	Litchmiota	637939981691912202	0	t	(1476,1354)	f	Grain	t	f	f	4125	Vilsi	15	0	f	Litchmiota	637939981691912202	f	f	2
220	2	{193,194,195,199,219}	Ghad	281967961189908482	400	f	(1204,360)	f	Fruits	f	f	f	2782	Yirbark	0	0	f	Ghad	281967961189908482	t	f	1
266	2	{259,260,262,289,369,484}	Litchmiota	637939981691912202	0	f	(1379,958)	f	Sugar	f	f	f	2797	Heisaari	15	0	f	Litchmiota	637939981691912202	f	f	1
737	2	{733,734,736,738,739}	Correlli	293518673417732098	0	f	(3103,331)	t	Chocolate	f	f	f	3111	Tamvi	0	0	f	Correlli	293518673417732098	f	f	3
751	2	{750,752,801}	Correlli	293518673417732098	0	t	(3213,142)	f	Fruits	f	f	f	3534	Străză	0	0	f	Correlli	293518673417732098	f	f	2
813	2	{811,812,814,816,820,821}	Correlli	293518673417732098	0	f	(3357,130)	f	Salt	f	f	f	3168	Huisuu	0	0	f	Correlli	293518673417732098	f	f	1
281	7	{275,276,277,280,282,283}	Ghad	281967961189908482	400	f	(1062,661)	f	Spices	f	f	f	155	Arirug	0	0	f	Ghad	281967961189908482	t	f	1
982	1	{977,978,981,983,987}	Nokoroth	428949783919460363	0	f	(3913,2880)	f	Glass	f	f	f	529	Kópafjörður	0	0	f	Nokoroth	428949783919460363	f	f	2
1077	5	{1070,1075,1076,1078,1084}	New Crea	692089085690380288	13	f	(3276,1902)	f	Precious Stones	f	f	f	712	Lienci	17	0	f	New Crea	692089085690380288	f	f	2
1191	0	{1177,1178,1190,1192,1193,1195,1196}	Blindgulf	967635049061163028	0	f	(2550,2577)	f	Tobacco	f	f	f	3206	Strănești	0	0	f	Blindgulf	967635049061163028	t	f	3
1031	0	{1028,1029,1030,1032,1033}		0	2440	f	(3938,1533)	t	Wool	f	f	f	4444	Dalnes	36	0	f		0	f	f	3
587	5	{573,574,575,586,588}	Tusail	844640695868194927	0	f	(995,2662)	f	Salt	f	f	f	773	Oroszna	23	0	f	Tusail	844640695868194927	f	f	2
449	0	{338,350}	Litchmiota	637939981691912202	0	t	(1735,1172)	t	Spices	t	f	f	4169	Karlsbæk	15	0	f	Litchmiota	637939981691912202	f	f	2
217	2	{199,200,210,213,216,218,219}	Ghad	281967961189908482	400	f	(1136,412)	t	Spices	f	f	f	3494	Lugwi	0	0	f	Ghad	281967961189908482	t	f	1
1097	0	{942,943,944,960,1096,1098,1099}	Khokand	905858887926816768	0	f	(2932,1512)	t	Fruits	f	f	f	4370	Łomkary	18	0	f	Khokand	905858887926816768	f	f	1
720	0	{719,721}		0	340	t	(3204,650)	f	Fur	f	f	f	4617	Blönnarnes	0	0	f		0	f	f	1
782	2	{779,780,781,783}	Correlli	293518673417732098	0	t	(3045,49)	f	Paper	f	f	f	3972	Uhernec	0	0	f	Correlli	293518673417732098	f	f	4
861	9	{859,860,862,863,864}	Blindgulf	0	456	f	(3739,207)	f	Ivory	f	f	f	228	Wadifer	0	0	f		0	f	f	3
340	5	{336,339,350,352,359}		0	1200	f	(1903,542)	f	Copper	f	f	f	868	Garðaseyri	0	0	f		0	f	f	4
719	0	{674,720,721,722}		0	298	t	(3136,643)	f	Spices	f	f	f	3521	Cupdul	0	0	f		0	f	f	2
1100	0	{1096,1099,1101,1128,1130}		0	336	f	(2923,1686)	f	Rare Wood	f	f	f	3698	Vopnaholt	0	0	f		0	f	f	2
73	0	{58,70,72,74}		0	258	t	(565,949)	f	Paper	f	f	f	3895	Þórsnes	0	0	f		0	f	f	1
314	2	{302,304,305,312,313,315}		0	357	f	(1667,457)	f	Fur	f	f	f	2764	Stukhólar	0	0	f		0	f	f	3
684	2	{678,681,683,685,686,716,717}		0	399	f	(2653,600)	f	Tin	f	f	f	3049	Garðaganes	0	0	f		0	f	f	1
274	2	{252,273,283,284,289}		0	378	f	(1028,812)	f	Wine	f	f	f	3429	Keflasós	0	0	f		0	f	f	4
308	2	{306,307,309,421,479,480}		0	378	f	(1633,637)	f	Iron	f	f	f	3387	Iana	0	0	f		0	f	f	4
431	2	{312,313,332,430,432}		0	383	f	(1762,578)	f	Sugar	f	f	f	4023	Grolupe	0	0	f		0	f	f	3
692	2	{689,691,693,694,702,703}		0	332	f	(2846,765)	f	Livestock	f	f	f	3668	Vipils	0	0	f		0	f	f	2
842	5	{837,838,839,843,846,847}		0	1058	f	(3490,146)	f	Copper	f	f	f	731	Aluklosta	0	0	f		0	f	f	1
919	0	{920,921}	Blindgulf	0	9002	t	(3422,637)	f	Tobacco	f	f	f	4501	Tel	0	0	f		0	f	f	2
259	5	{257,258,260,266,298,296,484}		0	1109	f	(1345,965)	f	Copper	f	f	f	820	Ziceni	0	0	f		0	f	f	2
1102	7	{1088,1095,1101,1103,1104,1107,1108}		0	123	f	(3036,1719)	f	Ivory	f	f	f	244	Prielsi	0	0	f		0	f	f	1
562	7	{561,563,564,565,570}		0	108	t	(1260,2646)	t	Rare Wood	f	f	f	173	Sigulda	0	0	f		0	f	f	2
1043	2	{1035,1036,1037,1042,1044,1047,1048}		0	345	f	(3659,1654)	t	Spices	f	f	f	3610	Piwice	0	0	f		0	f	f	4
1109	5	{1101,1107,1108,1110,1127}		0	1140	f	(3002,1875)	f	Raw Stone	f	f	f	633	Świmyśl	0	0	f		0	f	f	1
711	2	{709,710,712,713}	Khokand	905858887926816768	0	t	(2635,862)	t	Rare Wood	f	f	f	4090	Hólhólmur	18	0	f	Khokand	905858887926816768	f	f	1
190	9	{191}	Ghad	281967961189908482	650	t	(1352,229)	f	Fish	t	f	f	261	Buelita	0	0	f	Ghad	281967961189908482	f	f	2
810	2	{802,803,804,809,811,814,815}	Correlli	293518673417732098	0	f	(3314,133)	f	Fur	f	f	f	3019	Kory	0	0	f	Correlli	293518673417732098	f	f	1
100	0	{81,82,99,101,104}	Nanhai	899852149360566323	0	t	(538,740)	f	Wool	f	f	f	4317	Grigtos	0	0	f	Nanhai	899852149360566323	f	f	3
983	1	{977,982,984,986,987}	Nokoroth	428949783919460363	0	f	(4014,2946)	f	Paper	f	f	f	510	Drusštas	0	0	f	Nokoroth	428949783919460363	f	f	2
1205	2	{1203,1204,1206}	Blindgulf	967635049061163028	0	t	(2946,3110)	f	Copper	t	f	f	2672	Mažeiklute	0	0	f	Blindgulf	967635049061163028	t	f	1
1180	0	{1167,1171,1179,1181,1190}	Blindgulf	967635049061163028	0	f	(2766,2406)	f	Paper	f	f	f	4682	Dusetme	0	0	f	Blindgulf	967635049061163028	f	f	2
282	7	{280,281,283,284,433}	Ghad	281967961189908482	400	f	(983,670)	t	Glass	f	f	f	280	Begegaç	0	0	f	Ghad	281967961189908482	f	f	3
757	2	{755,756,758,806,807}	Correlli	293518673417732098	0	t	(3346,256)	f	Sugar	f	f	f	4141	Daugbrade	0	0	f	Correlli	293518673417732098	f	f	3
177	2	{160,176,178,182,183}	Ghad	281967961189908482	650	t	(1431,468)	t	Fruits	t	f	f	3301	Sarsier	0	0	f	Ghad	281967961189908482	t	f	1
98	0	{80,81,94,95,97,99}	Nanhai	899852149360566323	0	f	(558,832)	t	Ivory	f	f	f	4176	Ramysiejai	0	0	f	Nanhai	899852149360566323	f	f	2
1162	5	{1158,1159,1161,1163,1165,1166,1167,1182}	Blindgulf	967635049061163028	0	f	(2973,2383)	f	Salt	f	f	f	642	Piebunalski	0	0	f	Blindgulf	967635049061163028	f	f	2
284	7	{274,282,283,286,287}		0	145	f	(949,733)	t	Glass	f	f	f	279	Strenza	0	0	f		0	f	f	1
469	0	{468,470,473,488}	Litchmiota	637939981691912202	0	t	(1287,1359)	f	Wood	f	f	f	3659	Juanni	15	0	f	Litchmiota	637939981691912202	f	f	3
1208	2	{1207}	Nokoroth	428949783919460363	0	t	(3373,2977)	f	Salt	f	f	f	3698	Jurlava	0	0	f	Nokoroth	428949783919460363	f	f	1
269	0	{141,268,270,272,273}		0	297	f	(1010,918)	f	Tobacco	f	f	f	4286	Alodava	0	0	f		0	f	f	2
470	0	{468,469,471,472,488,489,490}		0	342	f	(1249,1379)	t	Tea and Coffee	f	f	f	3348	Valdone	0	0	f		0	f	f	3
9	0	{5,6,8,10,28,29}		0	375	f	(839,1253)	f	Livestock	f	f	f	3920	Limnda	0	0	f		0	f	f	4
834	5	{827,828,833,835}		0	1026	f	(3454,175)	f	Raw Stone	f	f	f	687	Varakgriva	0	0	f		0	f	f	2
1048	2	{1042,1043,1047}		0	373	f	(3670,1755)	t	Salt	f	f	f	3190	Chezno	0	0	f		0	f	f	4
268	0	{141,144,267,269,273,289}		0	312	f	(1042,925)	f	Cotton	f	f	f	3881	Chenowo	0	0	f		0	f	f	2
1047	2	{1043,1044,1041,1042,1046,1048,1049,1050}	New Crea	692089085690380288	0	f	(3598,1746)	t	Grain	f	f	f	3465	Bauslava	18	0	f	New Crea	692089085690380288	f	f	3
2	0	{1,3,4}		0	272	t	(862,1402)	f	Fruits	f	f	f	4301	Płowiec	0	0	f		0	f	f	1
998	0	{996,997,999,1000,1014}		0	379	t	(3839,1337)	f	Fur	f	f	f	4275	Soworzno	0	0	f		0	f	f	2
638	9	{636,637,639,640}		0	168	t	(2376,88)	f	Fish	f	f	f	270	Mažeikda	0	0	f		0	f	f	3
1146	0	{1145,1147,1152}	Khokand	905858887926816768	0	t	(2563,1814)	f	Wool	f	f	f	4443	Priecininkai	18	0	f	Khokand	905858887926816768	f	f	3
68	0	{60,61,67,69}		0	261	f	(722,909)	t	Grain	f	f	f	3178	Marijventis	0	0	f		0	f	f	1
880	9	{870,872,879,881,882}	Blindgulf	0	185	t	(4063,216)	f	Fur	f	f	f	181	Druskiai	0	0	f		0	f	f	1
472	0	{470,471,490,492,493}		0	0	t	(1215,1377)	f	Fur	f	f	f	4450	Jieztavas	0	0	f	Sarques	353107568547201035	f	f	2
657	9	{654,656,658}		0	185	t	(2772,70)	f	Fish	f	f	f	220	Rudišninka	0	0	f		0	f	f	2
149	2	{148,150,249,255,295,296}		0	368	f	(1240,916)	f	Fruits	f	f	f	3557	Utnai	0	0	f		0	f	f	3
953	0	{951,952,954,966,967}		0	257	f	(3415,1348)	t	Rare Wood	f	f	f	4935	Căliraolt	0	0	f		0	f	f	2
70	0	{58,59,60,69,71,72,73}		0	259	f	(616,927)	f	Wood	f	f	f	4220	Galanaia	0	0	f		0	f	f	1
293	2	{151,152,294,415}		0	344	f	(1321,801)	f	Chocolate	f	f	f	3164	Dolhadiru	0	0	f		0	f	f	1
1003	0	{967,968,990,1002,1004,1007}		0	271	f	(3524,1409)	f	Wood	f	f	f	3970	Ovilonta	0	0	f		0	f	f	2
1216	5	{698,699,700,702,1215,1217}		0	1022	f	(2770,783)	f	Copper	f	f	f	848	Gargbalis	0	0	f		0	f	f	1
482	0	{301,303,307,483}		0	382	f	(1595,562)	f	Fur	f	f	f	4832	Jurkule	0	0	f		0	f	f	2
54	0	{23,52,53,55,56,57,61,63}		0	332	f	(697,1012)	t	Tobacco	f	f	f	4387	Šventai	0	0	f		0	f	f	4
1039	2	{1024,1025,1026,1038,1040,1041}		0	397	f	(3837,1767)	t	Wood	f	f	f	3639	Vergiai	0	0	f		0	f	f	1
309	2	{306,308,310,311,421,422}		0	396	f	(1663,639)	f	Grain	f	f	f	2806	Ligatnas	0	0	f		0	f	f	2
378	1	{371,376,377,382,383}	Litchmiota	637939981691912202	1570	f	(1546,997)	f	Ivory	f	f	f	785	Vigazilani	0	0	f		0	f	f	2
823	9	{821,822,824,825,829,830}		0	226	t	(3404,112)	f	Fish	f	f	f	249	Gammaltorp	5	0	f		0	f	f	2
439	1	{438,440,465}	Litchmiota	637939981691912202	0	t	(2068,1476)	f	Spices	f	f	f	513	Ciatina	15	0	f	Litchmiota	637939981691912202	f	f	3
604	0	{601,602,603,605,606,616,617}	Tusail	844640695868194927	0	f	(801,2376)	t	Fruits	f	f	f	4358	Hønekim	23	0	f	Tusail	844640695868194927	f	f	2
538	0	{537,539,540,549}	Tusail	844640695868194927	0	t	(1298,2180)	f	Livestock	f	f	f	4414	Varros	23	0	f	Tusail	844640695868194927	f	f	1
956	0	{948,949,955,957,958,962,963}		0	390	f	(3195,1341)	f	Livestock	f	f	f	4368	Armănești	0	0	f		0	f	f	1
1118	5	{1080,1081,1116,1117,1119}		0	1212	f	(3191,2052)	f	Precious Stones	f	f	f	678	Grimhelle	0	0	f		0	f	f	2
530	0	{527,529,531,532,602}	Tusail	844640695868194927	0	t	(799,2245)	t	Tea and Coffee	f	f	f	4730	Farsøor	23	0	f	Tusail	844640695868194927	f	f	2
748	2	{745,746,747,749,753}	Correlli	293518673417732098	0	f	(3199,241)	f	Paper	f	f	f	2780	Harvern	0	0	f	Correlli	293518673417732098	f	f	3
296	2	{147,148,149,257,259,295,297,298}	Litchmiota	637939981691912202	0	f	(1271,949)	f	Fur	f	f	f	3363	Breksøra	15	0	f	Litchmiota	637939981691912202	t	f	1
199	9	{193,198,200,201,217,219,220}	Ghad	281967961189908482	400	f	(1170,326)	f	Fur	f	f	f	257	Rødhavn	0	0	f	Ghad	281967961189908482	t	f	4
742	2	{740,741,743,745}	Correlli	293518673417732098	0	t	(3107,225)	f	Iron	f	f	f	2823	Hokkbu	0	0	f	Correlli	293518673417732098	f	f	3
1012	0	{999,1010,1011,1013,1031,1032,1033,1034}		0	2057	f	(3825,1463)	f	Sugar	f	f	f	3378	Landskil	6	0	f		0	f	f	2
513	2	{512,514,515}		0	393	t	(526,1028)	f	Glass	f	f	f	3530	Ulsteinfjord	0	0	f		0	f	f	3
387	1	{360,361,362,386,444}	Litchmiota	637939981691912202	1480	f	(1453,1278)	f	Glass	f	f	f	740	Seyðissey	0	0	f		0	f	f	4
664	0	{661,663,665,666,667}		0	259	t	(2815,391)	f	Tobacco	f	f	f	4505	Snivo	0	0	f		0	f	f	2
1107	5	{1102,1104,1106,1108,1109,1110}		0	1271	f	(3081,1841)	f	Spices	f	f	f	718	Zlačín	0	0	f		0	f	f	1
189	9	{191,192,193}	Ghad	281967961189908482	400	f	(1271,277)	f	Glass	f	f	f	258	Alzilavega	0	0	f	Ghad	281967961189908482	f	f	3
979	2	{972,973,978,980,981}	Nokoroth	428949783919460363	0	t	(3796,2804)	f	Grain	f	f	f	3049	Kongsden	0	0	f	Nokoroth	428949783919460363	f	f	4
305	0	{304,306,310,312,314}		0	370	f	(1665,538)	f	Wood	f	f	f	4130	Stropky	0	0	f		0	f	f	1
790	5	{791,792}		0	1232	t	(3384,12)	f	Fish	f	f	f	619	Søgjøen	0	0	f		0	f	f	1
584	5	{581,582,583,612}	Tusail	844640695868194927	0	f	(855,2729)	f	Coal	f	f	f	780	Elvik	23	0	f	Tusail	844640695868194927	f	f	1
886	2	{884,885,887,889,890,891}	Blindgulf	0	5496	f	(4021,427)	f	Glass	f	f	f	2748	Rîșcamenca	0	0	f		0	f	f	4
151	0	{150,152,153,248,293,294,295}		0	335	f	(1269,859)	f	Paper	f	f	f	3528	Dudintár	0	0	f		0	f	f	2
768	0	{769}	Blindgulf	0	8486	t	(3535,449)	f	Grain	f	f	f	4243	Heraclymna	0	0	f		0	f	f	2
247	0	{149,243,244,246,248,249,250}		0	369	f	(1213,819)	t	Wool	f	f	f	3962	Oxelöhall	0	0	f		0	f	f	2
900	0	{895,896,899,901}	Blindgulf	0	8738	f	(3991,650)	t	Sugar	f	f	f	4369	Sinuicheon	0	0	f		0	f	f	3
920	0	{919,920,921,922}	Blindgulf	0	6542	t	(3472,695)	f	Paper	f	f	f	3271	Yahakonai	0	0	f		0	f	f	1
19	0	{12,13,16,18,20,28}		0	359	f	(718,1219)	t	Sugar	f	f	f	3258	Bollbro	0	0	f		0	f	f	3
881	9	{880,882,883}	Blindgulf	0	322	t	(4133,119)	f	Fur	f	f	f	240	Saysan	0	0	f		0	f	f	3
479	2	{308,420,421,478,480}		0	377	f	(1606,684)	f	Paper	f	f	f	4444	Orășa	0	0	f		0	f	f	1
301	0	{300,302,303,482,483}		0	399	f	(1604,513)	f	Glass	f	f	f	3701	Verdalhelle	0	0	f		0	f	f	3
1101	7	{1095,1096,1100,1102,1108,1109,1127,1128}		0	177	f	(2941,1706)	f	Paper	f	f	f	186	Arenstad	0	0	f		0	f	f	2
1026	2	{1021,1025,1027,1037,1038,1039}		0	300	f	(3909,1733)	t	Glass	f	f	f	2759	Grimhalsen	0	0	f		0	f	f	3
943	0	{932,942,944,1079}		0	352	f	(2961,1496)	t	Wool	f	f	f	3870	Asrum	0	0	f		0	f	f	3
286	2	{128,132,271,284,287,288}		0	339	f	(934,790)	t	Iron	f	f	f	3697	Finnros	0	0	f		0	f	f	1
1074	7	{1073,1075,1076,1086,1087,1089}		0	141	f	(3285,1786)	t	Paper	f	f	f	287	Tromvåg	0	0	f		0	f	f	3
577	7	{576,578,579}		0	169	t	(1044,2864)	f	Coal	f	f	f	245	Návičovo	0	0	f		0	f	f	3
1140	0	{1135,1136,1139,1141,1149}	Khokand	905858887926816768	0	f	(2635,1611)	t	Cotton	f	f	f	3274	Uppbo	18	0	f	Khokand	905858887926816768	f	f	2
343	5	{329,334,344}		0	1007	f	(1849,481)	f	Coal	f	f	f	747	Oxelötorp	0	0	f		0	f	f	2
302	0	{300,301,303,304,315}		0	262	t	(1604,481)	f	Tobacco	f	f	f	3227	Finburg	0	0	f		0	f	f	2
1137	0	{937,938,1136,1138,1139}	Khokand	905858887926816768	0	t	(2588,1499)	f	Fish	f	f	f	3377	Torsholm	18	0	f	Khokand	905858887926816768	f	f	4
256	2	{144,145,147,253,254,255,267}	Litchmiota	637939981691912202	0	f	(1125,965)	f	Spices	f	f	f	2987	Nibjah	15	0	f	Litchmiota	637939981691912202	t	f	1
540	0	{538,539,547,548,549}	Tusail	844640695868194927	0	f	(1370,2239)	f	Cotton	f	f	f	4249	Ignalbarkas	23	0	f	Tusail	844640695868194927	f	f	2
822	5	{812,813,821,823}		0	336	t	(3384,112)	f	Fish	f	f	f	895	Burdiac	5	0	f		0	f	f	3
775	2	{773,774,776,777}	Correlli	293518673417732098	0	t	(2998,171)	f	Paper	f	f	f	2576	Quditha	0	0	f	Correlli	293518673417732098	f	f	2
747	2	{738,746,748,753,754}	Correlli	293518673417732098	0	t	(3217,290)	f	Tea and Coffee	f	f	f	3030	Isolone	0	0	f	Correlli	293518673417732098	f	f	1
461	2	{373,374,396,397,298,458,460,462}		0	308	t	(1687,799)	f	Glass	f	f	f	3354	Ananruch	0	0	f		0	f	f	1
818	5	{816,817,819}	Correlli	293518673417732098	0	f	(3402,180)	f	Raw Stone	f	f	f	734	Eretrissos	0	0	f	Correlli	293518673417732098	f	f	4
1184	2	{1183,1185,1187}	Blindgulf	967635049061163028	0	t	(3168,2650)	f	Grain	t	f	f	3835	Thassofa	0	0	f	Blindgulf	967635049061163028	f	f	1
570	5	{561,562,565,569,571,572}		0	1155	f	(1229,2716)	f	Silver	f	f	f	848	Östlänge	0	0	f		0	f	f	2
1201	2	{1197,1198,1200,1202}	Blindgulf	967635049061163028	0	t	(2649,2889)	f	Copper	t	f	f	3471	Navathis	0	0	f	Blindgulf	967635049061163028	t	f	3
450	0	{448,449,451,452}	Litchmiota	637939981691912202	0	f	(1717,1138)	f	Wood	f	f	f	4080	Bohoi	15	0	f	Litchmiota	637939981691912202	f	f	1
476	2	{166,167,168,475,477,516}		0	304	f	(1519,702)	f	Copper	f	f	f	4033	Gamlesele	0	0	f		0	f	f	1
381	1	{379,380,382,385,445,446}	Litchmiota	637939981691912202	1558	f	(1573,1168)	f	Precious Stones	f	f	f	779	Dukvas	0	0	f		0	f	f	2
350	5	{338,339,340,342,346,349}		0	1004	f	(1899,517)	f	Coal	f	f	f	863	Sundbyvalla	0	0	f		0	f	f	1
756	2	{755,757}	Correlli	293518673417732098	0	t	(3359,295)	f	Paper	f	f	f	3098	Gato	0	0	f	Correlli	293518673417732098	f	f	3
226	2	{218,225,227,232}	Ghad	281967961189908482	650	t	(1174,502)	f	Paper	t	f	f	2934	Kärpina	0	0	f	Ghad	281967961189908482	t	f	2
963	0	{955,956,963,964,1091,1092}		0	366	f	(3243,1407)	f	Tobacco	f	f	f	3221	Uddekoga	0	0	f		0	f	f	2
1161	0	{1159,1160,1162,1182}	Blindgulf	967635049061163028	0	f	(3009,2410)	f	Ivory	f	f	f	3856	Limonum	0	0	f	Blindgulf	967635049061163028	f	f	2
1062	2	{1046,1049,1051,1061,1063,1064}	New Crea	692089085690380288	0	f	(3492,1786)	f	Grain	f	f	f	3430	Badekoyunlu	18	0	f	New Crea	692089085690380288	f	f	3
319	9	{317,318,320,325}		0	166	t	(1730,378)	f	Ivory	f	f	f	225	Henirad	0	0	f		0	f	f	1
120	7	{113,114,119,123,124}	Nanhai	899852149360566323	0	f	(772,612)	t	Silk	f	f	f	156	Pyongnam City	0	0	f	Nanhai	899852149360566323	f	f	1
608	2	{598,590,592,601,607,609}	Tusail	844640695868194927	0	f	(976,2450)	f	Tin	f	f	f	2534	Berchyn	23	0	f	Tusail	844640695868194927	f	f	1
1142	0	{1132,1133,1141,1143,1144,1147,1149}	Khokand	905858887926816768	0	f	(2689,1706)	t	Sugar	f	f	f	3138	Illinyk	18	0	f	Khokand	905858887926816768	f	f	1
58	0	{56,57,59,70,73}		0	399	t	(592,965)	t	Precious Goods	f	f	f	3872	Sivrikisla	0	0	f		0	f	f	4
424	0	{423,425,426,427,428}		0	338	f	(1771,659)	f	Grain	f	f	f	3462	Khorashtar	0	0	f		0	f	f	1
1113	5	{1111,1112,1114,1115,1127}		0	1198	f	(3078,1957)	t	Iron	f	f	f	849	Abayaan	0	0	f		0	f	f	2
701	5	{693,700,702}		0	1260	f	(2811,765)	f	Precious Stones	f	f	f	640	Österstad	0	0	f		0	f	f	3
94	0	{72,75,80,95,98}		0	385	f	(574,864)	t	Precious Goods	f	f	f	3005	Uzhhove	0	0	f		0	f	f	3
1153	7	{1124,1125,1154,1169,1170}		0	140	t	(2828,2126)	t	Paper	f	f	f	172	Bollhärad	0	0	f		0	f	f	1
50	0	{47,49,51,135,136,138}		0	333	f	(877,1051)	f	Tobacco	f	f	f	3085	Zbodiach	0	0	f		0	f	f	2
18	0	{16,17,19,20,21}		0	352	f	(650,1197)	f	Cotton	f	f	f	4618	Dalabey	0	0	f		0	f	f	1
1013	0	{999,1012,1014,1015,1016,1032}		0	283	f	(3915,1393)	f	Fruits	f	f	f	3281	Kocame	0	0	f		0	f	f	1
1028	2	{1019,1027,1031,1033,1037}		0	377	f	(3902,1627)	t	Grain	f	f	f	4244	Herist	0	0	f		0	f	f	3
353	2	{351,352,354,356,359}		0	306	t	(1951,520)	f	Chocolate	f	f	f	2585	Ahvalard	0	0	f		0	f	f	1
539	0	{538,540,541}	Tusail	844640695868194927	0	t	(1381,2180)	f	Glass	f	f	f	3253	Abylune	23	0	f	Tusail	844640695868194927	f	f	2
232	2	{226,227,233,238,241,277,278}	Ghad	281967961189908482	400	f	(1159,549)	f	Wine	f	f	f	4428	Kargava	0	0	f	Ghad	281967961189908482	t	f	2
1150	0	{1139,1147,1148,1149,1151}	Khokand	905858887926816768	0	f	(2565,1679)	f	Paper	f	f	f	3829	Bindugora	18	0	f	Khokand	905858887926816768	f	f	1
1136	0	{938,939,940,1135,1137,1139,1140}	Khokand	905858887926816768	0	f	(2653,1537)	t	Wool	f	f	f	3226	Altental	18	0	f	Khokand	905858887926816768	f	f	2
36	0	{34,35,37,36}		0	328	t	(1003,1172)	f	Wool	f	f	f	4363	Arsaistos	0	0	f		0	f	f	1
809	2	{804,805,807,808,810,815}	Correlli	293518673417732098	0	f	(3319,178)	f	Ivory	f	f	f	3184	Cassons	0	0	f	Correlli	293518673417732098	f	f	1
418	2	{390,391,416,419,434,483}		0	394	f	(1512,801)	f	Grain	f	f	f	3408	Kawa	0	0	f		0	f	f	1
47	0	{44,45,46,48,49,50,138}		0	340	f	(907,1087)	t	Livestock	f	f	f	3069	Iwagata	0	0	f		0	f	f	4
958	0	{945,956,957,958,961,962}		0	365	f	(3118,1366)	f	Livestock	f	f	f	4798	Masyamas	0	0	f		0	f	f	3
729	2	{668,728,730,733,734}	Correlli	293518673417732098	0	t	(3040,394)	t	Salt	f	f	f	3802	Tullanard	0	0	f	Correlli	293518673417732098	f	f	1
686	5	{678,684,687,685,696}		0	1060	f	(2768,629)	f	Spices	f	f	f	701	Hafsloekr	0	0	f		0	f	f	2
1176	0	{1175,1177,1192}	Blindgulf	967635049061163028	0	t	(2394,2441)	f	Paper	t	f	f	3428	Elmroda	0	0	f	Blindgulf	967635049061163028	f	f	1
1094	0	{960,961,1088,1089,1090,1095}		0	282	f	(3110,1573)	f	Rare Wood	f	f	f	3174	Alyros	0	0	f		0	f	f	4
973	2	{970,971,972,974,975,977,978,979}	Nokoroth	428949783919460363	0	f	(3907,2708)	f	Sugar	f	f	f	2958	Imblin	0	0	f	Nokoroth	428949783919460363	f	f	1
365	0	{362,363,366,367}	Litchmiota	637939981691912202	0	t	(1393,1165)	f	Wood	f	f	f	3417	Ilajov	15	0	f	Litchmiota	637939981691912202	f	f	1
52	0	{49,51,53,54,63,64,135}		0	347	f	(792,1017)	f	Paper	f	f	f	3792	Thamalala	0	0	f		0	f	f	1
819	5	{816,818,820,824,825}	Correlli	293518673417732098	0	f	(3409,153)	f	Spices	f	f	f	760	Mirabruševo	0	0	f	Correlli	293518673417732098	f	f	1
129	2	{127,128,131}		0	357	f	(868,787)	t	Wood	f	f	f	3419	Nueco	0	0	f		0	f	f	1
964	0	{954,955,963,965,1092}		0	358	f	(3285,1413)	f	Wood	f	f	f	4459	Quilica	0	0	f		0	f	f	2
1046	2	{1044,1045,1047,1049,1062}	New Crea	692089085690380288	50	f	(3494,1699)	f	Wood	f	f	f	4413	Nepturia	17	0	f	New Crea	692089085690380288	f	f	2
61	0	{54,55,60,62,63,67,68}		0	272	f	(731,970)	t	Paper	f	f	f	4558	Antsinimena	0	0	f		0	f	f	2
961	0	{958,959,960,962,1090,1091,1094}		0	334	f	(3128,1497)	f	Spices	f	f	f	3255	Heravala	0	0	f		0	f	f	3
833	5	{828,832,834}		0	1296	f	(3456,153)	f	Coal	f	f	f	698	Sherpenwerpen	0	0	f		0	f	f	1
323	9	{320,321,324,329,333,334}	Reasonable Nation Name	293518673417732098	164	f	(1784,421)	f	Glass	f	f	f	285	Navapotsavichy	0	0	f	Reasonable Nation Name	293518673417732098	f	f	2
1017	0	{1015,1016,1018,1030,1032}		0	2117	t	(4077,1447)	f	Wood	f	f	f	3425	Lofakulei	36	0	f		0	f	f	3
303	0	{301,302,304,306,307,482}		0	289	f	(1624,515)	f	Rare Wood	f	f	f	3536	Avignan	0	0	f		0	f	f	4
456	2	{375,454,455,457,458}		0	374	f	(1768,925)	f	Wine	f	f	f	4274	Orarica	0	0	f		0	f	f	1
455	2	{454,456,457,459}		0	359	t	(1834,918)	f	Tea and Coffee	f	f	f	3257	Slatizerce	0	0	f		0	f	f	1
981	1	{978,979,980,982,987}	Nokoroth	428949783919460363	0	t	(3807,2912)	f	Paper	f	f	f	568	Provarna	0	0	f	Nokoroth	428949783919460363	f	f	1
675	0	{673,674,676,677,688,689}		0	294	t	(2946,614)	f	Paper	f	f	f	4618	Ashof	0	0	f		0	f	f	4
689	2	{675,688,690,691,692,694}		0	334	t	(2880,731)	f	Salt	f	f	f	3511	Beltinci	0	0	f		0	f	f	2
231	2	{228,229,233,234,335}	Ghad	281967961189908482	400	f	(1260,556)	f	Tin	f	f	f	2943	Dusetkiai	0	0	f	Ghad	281967961189908482	t	f	4
271	0	{137,270,272,273,286,287,288}		0	321	f	(952,864)	t	Glass	f	f	f	3759	Tall-Qubayr	0	0	f		0	f	f	2
1167	0	{1162,1164,1165,1168,1171,1180,1181,1182}	Blindgulf	967635049061163028	0	f	(2831,2390)	f	Grain	f	f	f	3026	Kerdjerma	0	0	f	Blindgulf	967635049061163028	f	f	1
938	0	{934,937,939,1136,1137}	Khokand	905858887926816768	0	f	(2662,1453)	t	Paper	f	f	f	4772	Staventer	18	0	f	Khokand	905858887926816768	f	f	3
536	0	{535,537,552,596}	Tusail	844640695868194927	0	t	(1098,2149)	f	Paper	f	f	f	3928	Dianinum	23	0	f	Tusail	844640695868194927	f	f	2
887	0	{885,886,888,889,897}	Blindgulf	0	8926	t	(4068,495)	f	Paper	f	f	f	4463	Recalco	0	0	f		0	f	f	1
915	0	{913,914,916}	Blindgulf	0	8868	t	(3823,718)	f	Ivory	f	f	f	4434	Flushgard	0	0	f		0	f	f	2
869	9	{868,870,882,883}	Blindgulf	0	314	t	(4003,126)	f	Glass	f	f	f	157	Mekkadale	0	0	f		0	f	f	3
395	5	{396,411,412}		0	1294	f	(1638,821)	f	Salt	f	f	f	765	Al-Kareya	0	0	f		0	f	f	1
807	2	{757,805,806,808,809}	Correlli	293518673417732098	0	t	(3353,210)	f	Glass	f	f	f	3794	Salaclozi	0	0	f	Correlli	293518673417732098	f	f	4
828	5	{826,827,829,832,833,834}		0	1023	f	(3436,153)	f	Salt	f	f	f	865	Ctesirah	0	0	f		0	f	f	1
502	5	{488,500,501,503,506}		0	1092	f	(1249,1314)	f	Iron	f	f	f	724	Mongrieng	0	0	f		0	f	f	3
244	0	{239,240,243,245,246,247}		0	279	f	(1224,722)	t	Livestock	f	f	f	4280	Dammum	0	0	f		0	f	f	1
1104	5	{1102,1103,1105,1106,1107}		0	1029	f	(3112,1821)	f	Precious Stones	f	f	f	761	Nearey	0	0	f		0	f	f	1
53	0	{23,25,27,49,52,54}		0	273	f	(745,1084)	f	Tobacco	f	f	f	3511	Momadi	0	0	f		0	f	f	2
1049	2	{1046,1047,1050,1051,1062}	New Crea	692089085690380288	0	f	(3585,1771)	t	Chocolate	f	f	f	3891	Baršiná	18	0	f	New Crea	692089085690380288	f	f	3
467	0	{468,471}		0	353	t	(1287,1420)	t	Livestock	f	f	f	3999	Mongrom	0	0	f		0	f	f	2
568	5	{567}		0	1090	t	(1102,2765)	f	Fish	f	f	f	757	Rômbel	0	0	f		0	f	f	3
333	2	{321,322,323,332,334,335,432}		0	388	f	(1780,497)	f	Glass	f	f	f	3281	Põllin	0	0	f		0	f	f	1
294	2	{151,257,258,261,293,295,415}		0	359	f	(1327,864)	f	Sugar	f	f	f	2641	Karnor	0	0	f		0	f	f	2
966	0	{953,954,965,967,1004,1005}		0	324	f	(3380,1380)	t	Fur	f	f	f	3292	Tereni	0	0	f		0	f	f	3
201	9	{197,198,199,200,202,211}		0	267	t	(1161,272)	f	Fish	f	f	f	216	Sapoyut	0	0	f		0	f	f	1
292	0	{152,154,290,291,293,415,417,474}		0	332	f	(1336,747)	f	Grain	f	f	f	3579	Priegara	0	0	f		0	f	f	3
114	7	{112,113,120,119}	Nanhai	899852149360566323	0	f	(731,646)	f	Paper	f	f	f	199	Palangjung	0	0	f	Nanhai	899852149360566323	f	f	3
321	9	{317,320,322,323,333}		0	185	f	(1750,425)	f	Glass	f	f	f	216	Svärica	0	0	f		0	f	f	3
787	2	{786,788,789}	Correlli	293518673417732098	0	t	(3218,39)	f	Rare Wood	f	f	f	2804	Khushawai	0	0	f	Correlli	293518673417732098	f	f	1
394	5	{392,393,414}		0	1070	f	(1609,821)	f	Tin	f	f	f	849	Al-Hasyoun	0	0	f		0	f	f	1
179	0	{155,156,157,158,180,235}		0	324	f	(1345,589)	f	Rare Wood	f	f	f	4821	Probokal	0	0	f		0	f	f	4
784	2	{780,783,785}	Correlli	293518673417732098	0	t	(3099,53)	f	Iron	f	f	f	3336	Lhoklaya	0	0	f	Correlli	293518673417732098	f	f	2
1123	7	{1115,1120,1122,1124,1126,1155}	New Crea	692089085690380288	0	t	(3042,2131)	t	Glass	f	f	f	165	Balota	18	0	f	New Crea	692089085690380288	f	f	2
460	2	{458,459,461}		0	357	t	(1775,817)	f	Salt	f	f	f	4309	Pekandung	0	0	f		0	f	f	3
931	0	{928,930,932,933,934}	Khokand	905858887926816768	0	t	(2824,1359)	t	Cotton	f	f	f	3324	Bollbro	18	0	f	Khokand	905858887926816768	f	f	1
150	2	{149,151,248,295}		0	340	f	(1264,893)	f	Fruits	f	f	f	2878	Pekawang	0	0	f		0	f	f	3
1080	7	{1067,1068,1079,1081,1082,1118,1119}	New Crea	692089085690380288	0	t	(3252,2030)	f	Precious Goods	f	f	f	224	Purbel	18	0	f	New Crea	692089085690380288	f	f	3
425	0	{400,403,404,405,406,422,423,424,436}		0	290	f	(1744,704)	t	Ivory	f	f	f	4151	Djurskil	0	0	f		0	f	f	2
20	0	{18,19,21}		0	327	f	(718,1208)	t	Cotton	f	f	f	3566	Paloda	0	0	f		0	f	f	1
317	9	{316,318,319,321,322}		0	164	f	(1705,391)	f	Spices	f	f	f	218	Pemadiun	0	0	f		0	f	f	1
1204	2	{1187,1188,1202,1203,1205,1206}	Blindgulf	967635049061163028	0	t	(2988,2874)	f	Grain	t	f	f	3657	Xhataj	0	0	f	Blindgulf	967635049061163028	t	f	1
213	2	{208,209,210,212,214,216,217}	Ghad	281967961189908482	400	f	(1080,416)	f	Wood	f	f	f	4000	Moluos	0	0	f	Ghad	281967961189908482	f	f	2
492	5	{472,491,493,494,496}		0	0	f	(1197,1348)	f	Tin	f	f	f	796	Samagat	0	0	f	Sarques	353107568547201035	f	f	2
97	0	{95,96,98,99,102,105,107}	Nanhai	899852149360566323	0	f	(619,821)	t	Rare Wood	f	f	f	4120	Comspol	0	0	f	Nanhai	899852149360566323	f	f	3
746	2	{738,739,740,745,747,748}	Correlli	293518673417732098	0	f	(3177,265)	f	Wood	f	f	f	2997	Vaceni	0	0	f	Correlli	293518673417732098	f	f	1
590	2	{558,560,573,588,589,591,592,608}	Tusail	844640695868194927	0	f	(1042,2522)	f	Tobacco	f	f	f	3144	Sammar	23	0	f	Tusail	844640695868194927	f	f	2
369	1	{266,289,368,383,370,484}	Litchmiota	637939981691912202	0	f	(1388,972)	f	Precious Goods	f	f	f	756	Lukah	15	0	f	Litchmiota	637939981691912202	f	f	2
916	0	{898,899,913,915,917}	Blindgulf	0	9180	t	(3879,709)	f	Fur	f	f	f	4590	Miadananitra	0	0	f		0	f	f	1
866	9	{860,864,865,867,871}	Blindgulf	0	476	t	(3854,164)	f	Fish	f	f	f	238	Scabria	0	0	f		0	f	f	3
907	0	{876,906,908}	Blindgulf	0	7530	f	(3753,488)	f	Wood	f	f	f	3765	Trehać	0	0	f		0	f	f	2
906	0	{876,877,904,905,907,908,911}	Blindgulf	0	7232	f	(3789,472)	f	Wood	f	f	f	3616	Resdica	0	0	f		0	f	f	2
803	2	{800,801,802,804,810}	Correlli	293518673417732098	0	f	(3276,142)	f	Spices	f	f	f	3492	Polonihiv	0	0	f	Correlli	293518673417732098	f	f	2
739	2	{736,737,738,740,741,746}	Correlli	293518673417732098	0	f	(3112,295)	t	Wood	f	f	f	3314	Balasit	0	0	f	Correlli	293518673417732098	f	f	2
815	2	{808,809,810,814,816}	Correlli	293518673417732098	0	f	(3348,166)	f	Rare Wood	f	f	f	4231	Borgsås	0	0	f	Correlli	293518673417732098	t	f	3
1195	2	{1191,1193,1194,1196,1197,1199,1200}	Blindgulf	967635049061163028	0	f	(2511,2678)	f	Rare Wood	f	f	f	2792	Valabem	0	0	f	Blindgulf	967635049061163028	t	f	2
238	2	{232,233,237,239,240,241}		0	2106	f	(1199,612)	f	Glass	f	f	f	2992	Ulranta	0	0	f		0	f	f	1
1197	2	{1189,1195,1196,1198,1200,1201}	Blindgulf	967635049061163028	0	f	(2568,2714)	f	Wine	f	f	f	3022	Kroměkolov	0	0	f	Blindgulf	967635049061163028	t	f	1
1193	2	{1191,1192,1194,1195}	Blindgulf	967635049061163028	0	t	(2356,2637)	f	Livestock	t	f	f	3069	Krivotovo	0	0	f	Blindgulf	967635049061163028	t	f	2
204	9	{203,205}		0	150	f	(1080,313)	f	Fur	f	f	f	252	Hvolsfjörður	0	0	f		0	f	f	3
174	5	{159,161,173,175}	Ghad	281967961189908482	400	f	(1471,616)	f	Precious Stones	f	f	f	755	Halrup	0	0	f	Ghad	281967961189908482	f	f	2
210	2	{200,209,211,213,217}	Ghad	281967961189908482	400	f	(1107,355)	f	Livestock	f	f	f	2913	Friseen	0	0	f	Ghad	281967961189908482	f	f	1
162	0	{160,161,163,176,300}	Ghad	281967961189908482	400	f	(1507,495)	t	Cotton	f	f	f	4740	Kärva	0	0	f	Ghad	281967961189908482	t	f	1
402	5	{401,403,426,462}		0	0	t	(1802,727)	f	Silver	f	f	f	738	Guija	0	0	f	Orienta	913474777488973934	f	f	1
161	0	{159,160,162,163,164,173,174}	Ghad	281967961189908482	400	f	(1478,569)	t	Rare Wood	f	f	f	3731	Radkruojis	0	0	f	Ghad	281967961189908482	t	f	3
173	5	{161,164,167,172,174,175}	Ghad	281967961189908482	400	f	(1471,634)	f	Iron	f	f	f	692	Newney	0	0	f	Ghad	281967961189908482	f	f	3
694	5	{687,688,689,692,693,695,696}		0	1224	f	(2839,729)	f	Iron	f	f	f	688	Bhatok	0	0	f		0	f	f	1
601	2	{592,593,600,602,604,605,607,608}	Tusail	844640695868194927	0	f	(943,2376)	f	Tobacco	f	f	f	4453	Movone	23	0	f	Tusail	844640695868194927	f	f	1
882	9	{869,870,880,881,883}	Blindgulf	0	528	f	(4066,169)	f	Glass	f	f	f	264	Samovin	0	0	f		0	f	f	3
917	0	{899,901,902,913,916,918}	Blindgulf	0	9342	f	(3883,639)	f	Tea and Coffee	f	f	f	4671	Tullahal	0	0	f		0	f	f	3
888	0	{887,889,895,896,897}	Blindgulf	0	7432	f	(4052,542)	f	Wood	f	f	f	3716	Belmica	0	0	f		0	f	f	3
873	2	{865,871,872,874,878}	Blindgulf	0	5030	f	(3870,250)	f	Wood	f	f	f	2515	Chitunwayo	0	0	f		0	f	f	3
895	0	{888,889,894,896,900,901,902,903}	Blindgulf	0	6230	f	(3971,580)	f	Glass	f	f	f	3115	Fladbæk	0	0	f		0	f	f	2
759	2	{752,753,758,800,804,805,806}	Correlli	293518673417732098	0	f	(3278,184)	f	Livestock	f	f	f	2971	Huskhamn	0	0	f	Correlli	293518673417732098	f	f	1
749	2	{745,748,750,752,753}	Correlli	293518673417732098	0	f	(3217,205)	f	Fruits	f	f	f	3931	Pirakapi	0	0	f	Correlli	293518673417732098	f	f	2
863	2	{861,862,864,875}	Blindgulf	0	5856	t	(3694,283)	f	Paper	f	f	f	2928	Ivoryham	0	0	f		0	f	f	3
914	0	{912,913,915}	Blindgulf	0	7288	t	(3787,688)	t	Wool	f	f	f	3644	Rafhamloj	0	0	f		0	f	f	3
212	2	{207,208,213,214}	Ghad	281967961189908482	650	t	(1039,430)	f	Ivory	t	f	f	3517	Hollaweil	0	0	f	Ghad	281967961189908482	t	f	1
241	2	{232,238,240,242,276,277,278}		0	2989	f	(1159,625)	f	Livestock	f	f	f	3309	Þorlákshólmur	0	0	f		0	f	f	1
380	1	{379,381,446,447,448}	Litchmiota	637939981691912202	0	f	(1645,1078)	t	Glass	f	f	f	623	Wolrion	15	0	f	Litchmiota	637939981691912202	f	f	3
185	9	{184,186,221,222}	Ghad	281967961189908482	650	t	(1309,380)	t	Fish	t	f	f	233	Starkpeaks	0	0	f	Ghad	281967961189908482	f	f	3
223	2	{181,183,222,224,228,229,230}	Ghad	281967961189908482	400	f	(1303,461)	t	Chocolate	f	f	f	3749	Orova	0	0	f	Ghad	281967961189908482	t	f	1
733	2	{729,730,732,734,737,738}	Correlli	293518673417732098	0	f	(3103,349)	t	Tobacco	f	f	f	3460	Milišća	0	0	f	Correlli	293518673417732098	f	f	2
760	1	{0}	Litchmiota	637939981691912202	0	t	(2431,1384)	f	Glass	f	f	f	749	Ochadilsk	15	0	f	Litchmiota	637939981691912202	f	f	2
898	0	{897,899,916}		0	2286	t	(3935,722)	f	Glass	f	f	f	3128	Hînceriopol	0	0	f		0	f	f	3
1151	0	{1138,1139,1148,1150,1152}	Khokand	905858887926816768	0	t	(2484,1654)	f	Wood	f	f	f	4787	Concangis	18	0	f	Khokand	905858887926816768	f	f	2
927	0	{928,935,936}	Khokand	905858887926816768	0	t	(2626,1271)	t	Grain	f	f	f	4113	Limlanje	18	0	f	Khokand	905858887926816768	f	f	3
730	2	{726,727,728,729,731,732,733}	Correlli	293518673417732098	0	f	(3103,418)	t	Iron	f	f	f	2733	Oudenhout	0	0	f	Correlli	293518673417732098	f	f	4
453	2	{376,377,454}	Litchmiota	637939981691912202	0	t	(1721,990)	f	Wood	t	f	f	4025	Kulembu	15	0	f	Litchmiota	637939981691912202	f	f	3
805	2	{759,804,806,807,809}	Correlli	293518673417732098	0	f	(3316,209)	f	Wine	f	f	f	3378	Soavinatanana	0	0	f	Correlli	293518673417732098	f	f	3
416	2	{415,417,418,434,485}		0	2300	f	(1429,823)	f	Glass	f	f	f	3020	Ilorovo	0	0	f		0	f	f	2
44	0	{41,43,44,47,138,139,140,142}	"Soupy Zuzek"	552224320257130496	352	f	(985,1048)	f	Sugar	f	f	f	4847	Seltjarhöfn	14	0	f	"Soupy Zuzek"	552224320257130496	f	f	3
1183	0	{1160,1182,1184,1185}	Blindgulf	967635049061163028	0	t	(3121,2583)	f	Tea and Coffee	t	f	f	3195	Ahvaft	0	0	f	Blindgulf	967635049061163028	t	f	1
1194	2	{1193,1195,1199}	Blindgulf	967635049061163028	0	t	(2297,2729)	f	Chocolate	t	f	f	4018	Ulricellefteå	0	0	f	Blindgulf	967635049061163028	t	f	1
372	1	{370,371,373,376,389,390,391,392}		0	580	f	(1552,857)	f	Glass	f	f	f	507	Reniche	4	0	f		0	f	f	1
224	2	{221,222,223,225,227,228}	Ghad	281967961189908482	400	f	(1244,457)	t	Fruits	f	f	f	2502	Behbast	0	0	f	Ghad	281967961189908482	t	f	1
361	0	{360,387,443,444}	Litchmiota	637939981691912202	9512	f	(1456,1327)	f	Ivory	f	f	f	4756	Narzon	0	0	f		0	f	f	4
202	9	{201,203,211}		0	156	t	(1127,292)	f	Fish	f	f	f	235	Jauncut	0	0	f		0	f	f	4
877	2	{874,875,876,878,891,892,905,906}	Blindgulf	0	6718	f	(3807,394)	f	Livestock	f	f	f	3359	Vatroca	0	0	f		0	f	f	3
890	0	{886,889,891,892,893,894}	Blindgulf	0	8782	f	(3967,425)	f	Cotton	f	f	f	4391	Þórsnesi	0	0	f		0	f	f	1
289	2	{262,264,265,266,369,370,386,463}	Litchmiota	637939981691912202	0	f	(1420,927)	f	Livestock	f	f	f	2729	Kilaqqez	15	0	f	Litchmiota	637939981691912202	f	f	4
860	9	{859,861,864,865,866}	Blindgulf	0	390	t	(3792,175)	f	Fish	f	f	f	195	Abgeva	0	0	f		0	f	f	2
883	9	{869,881,882}	Blindgulf	0	216	t	(4068,106)	f	Glass	f	f	f	193	Verdaljøen	0	0	f		0	f	f	3
426	0	{402,403,424,425,427}		0	0	t	(1793,686)	t	Rare Wood	f	f	f	4699	国城市	0	0	f	Orienta	913474777488973934	f	f	1
910	0	{908,911,912}	Blindgulf	0	6485	t	(3690,531)	f	Glass	f	f	f	3482	Dunajňava	0	0	f		0	f	f	1
401	5	{400,402,403,462}		0	0	f	(1782,745)	f	Precious Stones	f	f	f	724	Alsschau	0	0	f	Orienta	913474777488973934	f	f	2
868	9	{867,869,870,871}	Blindgulf	0	300	t	(3928,108)	f	Precious Goods	f	f	f	150	Sivriyayla	0	0	f		0	f	f	4
493	0	{472,492,494}		0	0	t	(1177,1377)	f	Glass	f	f	f	3890	Kanochang	0	0	f	Sarques	353107568547201035	f	f	2
801	2	{751,752,800,803,802}	Correlli	293518673417732098	0	t	(3240,126)	f	Fish	f	f	f	4080	Brønnøystrøm	0	0	f	Correlli	293518673417732098	f	f	3
754	2	{747,753,755,758}	Correlli	293518673417732098	0	t	(3247,301)	f	Grain	f	f	f	2785	Sabigums	0	0	f	Correlli	293518673417732098	f	f	2
1190	0	{1178,1179,1180,1181,1182,1186,1189,1191,1196}	Blindgulf	967635049061163028	0	f	(2761,2518)	f	Wool	f	f	f	3849	Kalintsa	0	0	f	Blindgulf	967635049061163028	f	f	4
589	2	{588,590,608,609}	Tusail	844640695868194927	0	f	(994,2536)	f	Grain	f	f	f	4162	Barekawa	23	0	f	Tusail	844640695868194927	f	f	4
602	0	{529,530,532,600,601,603,604}	Tusail	844640695868194927	0	f	(848,2326)	t	Wool	f	f	f	3508	Salacele	23	0	f	Tusail	844640695868194927	f	f	4
726	0	{725,727,730,731}	Correlli	293518673417732098	0	t	(3199,459)	t	Sugar	f	f	f	4037	Rausoka	0	0	f	Correlli	293518673417732098	f	f	1
902	0	{895,901,903,904,917,918}	Blindgulf	0	9508	f	(3890,558)	t	Glass	f	f	f	4754	Ocosingo	0	0	f		0	f	f	4
874	2	{864,865,873,875,877,878}	Blindgulf	0	6862	f	(3805,295)	f	Paper	f	f	f	3431	Tomadura	0	0	f		0	f	f	2
899	0	{896,897,898,900,901,917}	Blindgulf	0	8632	f	(3951,697)	t	Tea and Coffee	f	f	f	4316	Kemeca	0	0	f		0	f	f	1
725	0	{724,724,726,727}	Correlli	293518673417732098	0	t	(3184,506)	t	Fish	f	f	f	4520	Etadfa	0	0	f	Correlli	293518673417732098	t	f	3
728	0	{668,670,671,724,727,729,730}	Correlli	293518673417732098	0	f	(3053,450)	t	Wool	f	f	f	4053	Śląnin	0	0	f	Correlli	293518673417732098	f	f	1
731	2	{726,730,732}	Correlli	293518673417732098	0	f	(3220,416)	t	Salt	f	f	f	4417	Tjendepet	0	0	f	Correlli	293518673417732098	f	f	1
727	0	{724,725,726,728,730}	Correlli	293518673417732098	0	f	(3114,466)	t	Grain	f	f	f	4806	Ergen	0	0	f	Correlli	293518673417732098	f	f	2
458	2	{374,456,457,459,460,461}		0	325	f	(1759,866)	f	Livestock	f	f	f	2816	Banmat	0	0	f		0	f	f	1
734	2	{729,733,735,736,737}	Correlli	293518673417732098	0	t	(3033,344)	f	Grain	f	f	f	4275	Zhytkakaw	0	0	f	Correlli	293518673417732098	f	f	2
109	2	{103,106,108,110,111,112,113,114}	Nanhai	899852149360566323	0	f	(661,729)	f	Tea and Coffee	f	f	f	3760	Patangor	0	0	f	Nanhai	899852149360566323	f	f	2
485	2	{265,298,388,389,390,415,416,462}		0	2252	f	(1453,846)	f	Paper	f	f	f	2776	Mandujang	0	0	f		0	f	f	1
865	9	{864,866,871,873,874}	Blindgulf	0	500	f	(3847,223)	f	Fur	f	f	f	250	Trbojice	0	0	f		0	f	f	1
876	0	{875,877,906,907,908}	Blindgulf	0	9466	t	(3726,416)	f	Spices	f	f	f	4733	Molepodibe	0	0	f		0	f	f	2
911	0	{904,906,908,910,912,913}	Blindgulf	0	3354	f	(3762,558)	f	Spices	f	f	f	3296	Buhuşiţa	0	0	f		0	f	f	2
867	9	{866,868,871}	Blindgulf	0	406	t	(3883,110)	f	Glass	f	f	f	203	Sobalevu	0	0	f		0	f	f	4
376	1	{371,372,373,375,377,378,453,454}		0	847	f	(1600,893)	f	Glass	f	f	f	766	Jezejevec	15	0	f		0	f	f	1
195	9	{186,187,194,219,221,220}	Ghad	281967961189908482	400	f	(1249,344)	f	Glass	f	f	f	299	Wrycanyon	0	0	f	Ghad	281967961189908482	f	f	1
176	2	{160,162,177}	Ghad	281967961189908482	650	t	(1462,463)	f	Tin	t	f	f	4284	Pärpina	0	0	f	Ghad	281967961189908482	t	f	1
523	2	{520,521,524}	Tusail	844640695868194927	0	t	(499,1980)	f	Rare Wood	t	f	f	2538	Hraunaheior	23	0	f	Tusail	844640695868194927	f	f	3
556	7	{554,555,557,558,559}	Tusail	844640695868194927	0	t	(1161,2452)	f	Silk	f	f	f	177	Tsunareth	23	0	f	Tusail	844640695868194927	f	f	3
524	2	{521,522,523,525,526}	Tusail	844640695868194927	0	t	(425,2113)	f	Livestock	f	f	f	3964	Vierbonne	23	0	f	Tusail	844640695868194927	f	f	2
551	0	{549,550,552,553,554}	Tusail	844640695868194927	0	f	(1282,2333)	f	Grain	f	f	f	3398	Kiviõna	23	0	f	Tusail	844640695868194927	f	f	1
553	0	{551,552,554,555,595,596}	Tusail	844640695868194927	0	f	(1204,2311)	f	Livestock	f	f	f	3525	Kashavar	23	0	f	Tusail	844640695868194927	f	f	3
788	2	{787,789}	Correlli	293518673417732098	0	t	(3253,38)	f	Tobacco	f	f	f	4495	Belabatangan	0	0	f	Correlli	293518673417732098	f	f	1
543	0	{542,544,545}		0	1406	t	(1600,2326)	f	Fur	f	f	f	4244	Eyrarjarhverfi	9	0	f		0	f	f	1
544	1	{543,545}		0	852	t	(1629,2385)	f	Glass	f	f	f	785	Almacos	9	0	f		0	f	f	2
545	1	{541,542,543,544,546,647}		0	771	t	(1510,2376)	f	Ivory	f	f	f	624	Sabidava	9	0	f		0	f	f	1
554	0	{550,551,553,555,556}	Tusail	844640695868194927	0	t	(1228,2396)	f	Livestock	f	f	f	3513	Jīnzi	23	0	f	Tusail	844640695868194927	f	f	2
1200	2	{1195,1197,1199,1200,1201}	Blindgulf	967635049061163028	0	t	(2502,2907)	f	Wood	t	f	f	3040	Maigapu	0	0	f	Blindgulf	967635049061163028	t	f	2
547	1	{540,541,545,546,548}		0	663	t	(1408,2344)	f	Ivory	f	f	f	672	Ylövala	8	0	f		0	f	f	1
1011	0	{999,1000,1001,1010,1012}	New Crea	692089085690380288	20	f	(3704,1411)	f	Cotton	f	f	f	4848	Gipuscay	17	0	f	New Crea	692089085690380288	f	f	3
1134	0	{940,1098,1132,1133,1135}	Khokand	905858887926816768	0	f	(2781,1571)	t	Livestock	f	f	f	4443	Aungbwe	18	0	f	Khokand	905858887926816768	f	f	3
558	7	{556,557,559,560,590,591}	Tusail	844640695868194927	0	f	(1120,2513)	f	Spices	f	f	f	160	Tatak	23	0	f	Tusail	844640695868194927	f	f	1
586	5	{575,580,581,585,587,588,611}	Tusail	844640695868194927	0	f	(961,2676)	f	Salt	f	f	f	696	Mareos	23	0	f	Tusail	844640695868194927	f	f	3
1173	0	{1172,1174}	Blindgulf	967635049061163028	0	t	(2522,2277)	f	Grain	f	f	f	4628	Aungde	0	0	f	Blindgulf	967635049061163028	f	f	2
611	5	{585,586,588,610,612}	Tusail	844640695868194927	0	f	(900,2646)	f	Silver	f	f	f	725	Ngache	23	0	f	Tusail	844640695868194927	f	f	2
147	0	{145,146,148,255,256,296}	Litchmiota	637939981691912202	0	f	(1201,974)	t	Tea and Coffee	f	f	f	3589	Kakant	15	0	f	Litchmiota	637939981691912202	t	f	2
255	2	{147,148,149,249,254,256}	Litchmiota	637939981691912202	0	f	(1192,934)	t	Fruits	f	f	f	2775	Senneko	15	0	f	Litchmiota	637939981691912202	t	f	1
620	1	{613,618,619}	Tusail	844640695868194927	0	t	(666,2576)	f	Paper	f	f	f	642	Nathenkota	23	0	f	Tusail	844640695868194927	f	f	1
557	7	{555,556,558,591,594,595}	Tusail	844640695868194927	0	f	(1120,2432)	f	Glass	f	f	f	183	Grervara	23	0	f	Tusail	844640695868194927	f	f	1
588	2	{573,586,587,590,589,609,611}	Tusail	844640695868194927	0	f	(958,2578)	f	Fur	f	f	f	3688	Meoalfell	23	0	f	Tusail	844640695868194927	f	f	3
548	0	{540,547,549,550}	Tusail	844640695868194927	0	t	(1354,2304)	f	Glass	f	f	f	3169	Aknibe	23	0	f	Tusail	844640695868194927	f	f	1
613	1	{583,610,612,614,619,620}	Tusail	844640695868194927	0	t	(727,2650)	f	Paper	f	f	f	736	Cajemoros	23	0	f	Tusail	844640695868194927	f	f	4
550	0	{548,549,551,554}	Tusail	844640695868194927	0	t	(1298,2394)	f	Cotton	f	f	f	4001	Dreadwall	23	0	f	Tusail	844640695868194927	f	f	4
1096	0	{960,1095,1097,1099,1100,1101}		0	372	f	(2982,1562)	f	Grain	f	f	f	3972	Cidan	0	0	f		0	f	f	3
957	0	{945,946,947,948,956,958}		0	363	f	(3130,1316)	f	Livestock	f	f	f	3005	Namhpadan	0	0	f		0	f	f	2
862	2	{857,859,861,863}	Blindgulf	0	7104	t	(3683,220)	f	Livestock	f	f	f	3552	Kisrimeru	0	0	f		0	f	f	1
707	0	{690,691,706,708}		0	396	t	(2959,954)	f	Ivory	f	f	f	3979	Nyaungshi	0	0	f		0	f	f	4
609	2	{588,589,607,608,610,615}	Tusail	844640695868194927	0	f	(880,2520)	f	Paper	f	f	f	3693	Chitiza	23	0	f	Tusail	844640695868194927	f	f	2
83	0	{82,84,85,101}	Nanhai	899852149360566323	0	t	(457,785)	f	Wood	f	f	f	4683	Dumadal	0	0	f	Nanhai	899852149360566323	f	f	3
546	1	{545,547}		0	885	t	(1440,2419)	f	Precious Stones	f	f	f	767	Molbak	9	0	f		0	f	f	4
555	7	{553,554,556,557,596}	Tusail	844640695868194927	0	f	(1186,2387)	f	Paper	f	f	f	252	Osstrøm	23	0	f	Tusail	844640695868194927	f	f	2
329	9	{323,324,328,330,334,343,344}		0	130	f	(1836,434)	f	Glass	f	f	f	210	Samamoc	0	0	f		0	f	f	2
566	5	{564,565,567,569}		0	1005	t	(1219,2788)	f	Tin	f	f	f	600	Mabalacurong	0	0	f		0	f	f	1
452	0	{450,451}	Litchmiota	637939981691912202	0	t	(1699,1035)	f	Glass	t	f	f	4256	Malume	15	0	f	Litchmiota	637939981691912202	f	f	2
451	0	{449,450,452}	Litchmiota	637939981691912202	0	t	(1750,1125)	f	Precious Goods	t	f	f	3388	Dubtowel	15	0	f	Litchmiota	637939981691912202	f	f	2
448	0	{380,447,449,450}	Litchmiota	637939981691912202	0	t	(1683,1168)	t	Livestock	t	f	f	4731	Însudud	15	0	f	Litchmiota	637939981691912202	f	f	3
463	5	{289,370,388,485}	Litchmiota	637939981691912202	0	f	(1483,889)	f	Salt	f	f	f	789	Márrol	15	0	f	Litchmiota	637939981691912202	f	f	1
912	0	{910,911,913,914}	Blindgulf	0	3507	t	(3730,637)	f	Grain	f	f	f	4824	Booriwa	0	0	f		0	f	f	3
246	0	{153,154,155,244,245,247,248}		0	296	f	(1249,747)	t	Tea and Coffee	f	f	f	3469	Taguvotas	0	0	f		0	f	f	2
603	0	{528,529,602,604,617}	Tusail	844640695868194927	0	f	(760,2358)	t	Grain	f	f	f	4702	Chervonivka	23	0	f	Tusail	844640695868194927	f	f	3
591	2	{557,558,590,592,593,594}	Tusail	844640695868194927	0	f	(1087,2446)	f	Spices	f	f	f	3769	Mjölsås	23	0	f	Tusail	844640695868194927	f	f	3
563	7	{562,564}		0	135	t	(1314,2702)	f	Paper	f	f	f	190	Galisay	0	0	f		0	f	f	2
626	2	{627,628}		0	333	t	(2313,351)	f	Wood	f	f	f	3246	Escapalay	0	0	f		0	f	f	1
993	0	{992,994}		0	344	t	(3793,1215)	f	Fur	f	f	f	4040	Antipi	0	0	f		0	f	f	3
1027	2	{1019,1020,1026,1028}		0	317	f	(3929,1717)	t	Livestock	f	f	f	2754	Baido	0	0	f		0	f	f	3
1202	2	{1188,1198,1201,1203,1204}	Blindgulf	967635049061163028	0	t	(2713,2977)	f	Ivory	t	f	f	3030	Hobulla	0	0	f	Blindgulf	967635049061163028	t	f	3
974	2	{970,973,975}	Nokoroth	428949783919460363	0	t	(4077,2667)	f	Livestock	f	f	f	3003	Cragool	0	0	f	Nokoroth	428949783919460363	f	f	1
932	0	{931,933,942,943,944}	Khokand	905858887926816768	0	t	(2914,1402)	t	Fruits	f	f	f	3247	Goulbick	18	0	f	Khokand	905858887926816768	f	f	3
397	5	{396,398,399,407,461}		0	1112	f	(1685,787)	f	Spices	f	f	f	718	Rowvegie	0	0	f		0	f	f	2
242	2	{240,241,243,251,276}		0	2096	f	(1145,724)	f	Fruits	f	f	f	3110	Situmri	0	0	f		0	f	f	4
1149	0	{1139,1140,1141,1142,1147,1150}	Khokand	905858887926816768	0	f	(2613,1661)	t	Rare Wood	f	f	f	4197	Lekamawai	18	0	f	Khokand	905858887926816768	f	f	2
1174	0	{1172,1173,1175}	Blindgulf	967635049061163028	0	t	(2497,2299)	f	Paper	f	f	f	4759	Lumika	0	0	f	Blindgulf	967635049061163028	f	f	2
596	0	{535,536,552,553,595,597}	Tusail	844640695868194927	0	f	(1125,2243)	f	Livestock	f	f	f	3659	Sisowai	23	0	f	Tusail	844640695868194927	f	f	2
258	5	{257,259,260,261,294}		0	1102	f	(1341,929)	f	Gold	f	f	f	756	Benuamaiku	0	0	f		0	f	f	3
991	0	{989,990,992,997,1000,1001}		0	328	t	(3702,1260)	f	Wood	f	f	f	4428	Tabuiki	0	0	f		0	f	f	1
1032	0	{1012,1013,1016,1017,1030,1031,1033}		0	2995	f	(3942,1485)	t	Wood	f	f	f	3927	Aeneamaiaki	36	0	f		0	f	f	4
200	9	{199,201,210,211,217,219}	Ghad	281967961189908482	400	f	(1143,351)	f	Fur	f	f	f	286	Manatangata	0	0	f	Ghad	281967961189908482	f	f	3
549	0	{537,538,540,548,550,551,552}	Tusail	844640695868194927	0	f	(1321,2268)	f	Grain	f	f	f	4244	Katua	23	0	f	Tusail	844640695868194927	f	f	2
651	9	{649,650,652,653}		0	146	t	(2644,43)	f	Glass	f	f	f	181	Tebwatao	0	0	f		0	f	f	2
37	0	{36,38,42,43,45,46}		0	268	t	(1017,1127)	f	Tobacco	f	f	f	3030	Faiwald	0	0	f		0	f	f	1
517	0	{252,253,267,268,273,274}		0	321	f	(1071,871)	f	Glass	f	f	f	4413	Pararaumu	0	0	f		0	f	f	1
67	0	{60,61,62,66,68}		0	327	f	(754,927)	t	Grain	f	f	f	4761	Makelaga	0	0	f		0	f	f	3
421	2	{308,309,406,407,408,420,422,479}		0	318	f	(1647,688)	f	Iron	f	f	f	4340	Savaleolo	0	0	f		0	f	f	2
962	0	{956,958,961,963,1091}		0	382	f	(3198,1420)	f	Wood	f	f	f	3201	Guatasaga	0	0	f		0	f	f	1
488	1	{469,470,473,487,489,501,502,503}		0	132	f	(1273,1316)	f	Paper	f	f	f	730	Ninipunga	0	0	f		0	f	f	1
71	0	{69,70,72,95,96}		0	335	f	(659,864)	t	Cotton	f	f	f	4803	Elsons Abyss	0	0	f		0	f	f	2
270	0	{137,139,140,141,269,271,272}		0	321	f	(967,949)	f	Spices	f	f	f	4659	Eastrock Cliffs	0	0	f		0	f	f	2
496	1	{492,494,497,498,499,505}		0	0	t	(1147,1294)	f	Ivory	f	f	f	533	Garenne County	0	0	f	Sarques	353107568547201035	f	f	2
\.


--
-- PostgreSQL database dump complete
--


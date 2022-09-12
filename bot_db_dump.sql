--
-- PostgreSQL database dump
--

-- Dumped from database version 13.3
-- Dumped by pg_dump version 13.3

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
-- Name: blacklist; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.blacklist (
    user_id bigint,
    status text,
    end_time timestamp without time zone,
    mod_id bigint,
    reason text,
    active boolean DEFAULT true,
    action_id bigint,
    action_date date
);


ALTER TABLE public.blacklist OWNER TO postgres;

--
-- Name: cnc_data; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.cnc_data (
    data_name text,
    data_value integer
);


ALTER TABLE public.cnc_data OWNER TO postgres;

--
-- Name: cnc_events; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.cnc_events (
    name text,
    effects text,
    weight integer DEFAULT 100,
    type text,
    duration integer DEFAULT 1,
    turns integer DEFAULT 0
);


ALTER TABLE public.cnc_events OWNER TO postgres;

--
-- Name: cnc_modifiers; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.cnc_modifiers (
    user_id bigint,
    wool_mod double precision DEFAULT 0,
    fish_mod double precision DEFAULT 0,
    fur_mod double precision DEFAULT 0,
    grain_mod double precision DEFAULT 0,
    livestock_mod double precision DEFAULT 0,
    salt_mod double precision DEFAULT 0,
    wine_mod double precision DEFAULT 0,
    copper_mod double precision DEFAULT 0,
    iron_mod double precision DEFAULT 0,
    precious_goods_mod double precision DEFAULT 0,
    spices_mod double precision DEFAULT 0,
    tea_and_coffee_mod double precision DEFAULT 0,
    chocolate_mod double precision DEFAULT 0,
    cotton_mod double precision DEFAULT 0,
    sugar_mod double precision DEFAULT 0,
    tobacco_mod double precision DEFAULT 0,
    dyes_mod double precision DEFAULT 0,
    silk_mod double precision DEFAULT 0,
    rare_wood_mod double precision DEFAULT 0,
    glass_mod double precision DEFAULT 0,
    paper_mod double precision DEFAULT 0,
    precious_stones_mod double precision DEFAULT 0,
    coal_mod double precision DEFAULT 0,
    gold_mod double precision DEFAULT 0,
    fruits_mod double precision DEFAULT 0,
    raw_stone_mod double precision DEFAULT 0,
    wood_mod double precision DEFAULT 0,
    silver_mod double precision DEFAULT 0,
    tin_mod double precision DEFAULT 0,
    ivory_mod double precision DEFAULT 0,
    income_mod double precision DEFAULT 1,
    tax_mod double precision DEFAULT 1,
    workshop_production_mod double precision DEFAULT 1,
    production_mod double precision DEFAULT 1,
    trade_route double precision DEFAULT 0,
    trade_route_efficiency_mod double precision DEFAULT 1,
    national_unrest_suppression_efficiency_mod double precision DEFAULT 1,
    local_unrest_suppression_efficiency_mod double precision DEFAULT 1,
    defense_level double precision DEFAULT 1,
    attack_level double precision DEFAULT 1,
    army_limit bigint DEFAULT 15000,
    movement_cost_mod double precision DEFAULT 1,
    manpower_mod double precision DEFAULT 1,
    troop_upkeep_mod double precision DEFAULT 1,
    research_mod double precision DEFAULT 1
);


ALTER TABLE public.cnc_modifiers OWNER TO postgres;

--
-- Name: cnc_researching; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.cnc_researching (
    user_id bigint,
    tech text,
    turns integer DEFAULT 0
);


ALTER TABLE public.cnc_researching OWNER TO postgres;

--
-- Name: cnc_tech; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.cnc_tech (
    name text,
    effect text,
    prerequisites text,
    description text,
    exclusive text,
    field text,
    image text,
    cords point
);


ALTER TABLE public.cnc_tech OWNER TO postgres;

--
-- Name: cncusers; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.cncusers (
    user_id bigint,
    username text,
    usercolor text,
    resources bigint,
    focus text,
    undeployed bigint,
    moves integer DEFAULT 0,
    manpower bigint DEFAULT 3000,
    maxmanpower bigint DEFAULT 3000,
    taxation integer DEFAULT 10,
    military_upkeep integer DEFAULT 10,
    public_services integer DEFAULT 15,
    national_unrest integer DEFAULT 0,
    capital integer DEFAULT 0,
    event text DEFAULT ''::text,
    great_power boolean DEFAULT false,
    great_power_score bigint DEFAULT 0,
    capital_move integer DEFAULT 0,
    researched text[],
    event_duration integer DEFAULT 0,
    trade_route_limit integer DEFAULT 0,
    citylimit integer DEFAULT 0,
    portlimit integer DEFAULT 0,
    fortlimit integer DEFAULT 0
);


ALTER TABLE public.cncusers OWNER TO postgres;

--
-- Name: currency; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.currency (
    name text,
    worth double precision,
    userid bigint,
    symbol text DEFAULT ''::text,
    backed text DEFAULT ''::text,
    server_id bigint,
    nation text DEFAULT ''::text
);


ALTER TABLE public.currency OWNER TO postgres;

--
-- Name: interactions; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.interactions (
    id bigint,
    type text,
    sender text,
    sender_id bigint,
    recipient text,
    recipient_id bigint,
    terms text,
    active boolean
);


ALTER TABLE public.interactions OWNER TO postgres;

--
-- Name: maxcas; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.maxcas (
    modifier double precision,
    "1" double precision,
    "2" double precision,
    "3" double precision,
    "4" double precision,
    "5" double precision,
    "6" double precision
);


ALTER TABLE public.maxcas OWNER TO postgres;

--
-- Name: mod_logs; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.mod_logs (
    action text,
    reason text,
    mod_id bigint,
    id bigint
);


ALTER TABLE public.mod_logs OWNER TO postgres;

--
-- Name: pending_interactions; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.pending_interactions (
    id bigint,
    type text,
    sender text,
    sender_id bigint,
    recipient text,
    recipient_id bigint,
    terms text
);


ALTER TABLE public.pending_interactions OWNER TO postgres;

--
-- Name: provinces; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.provinces (
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


ALTER TABLE public.provinces OWNER TO postgres;

--
-- Name: recruitment; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.recruitment (
    user_id bigint,
    template text,
    sent bigint DEFAULT 0,
    sent_this_month integer DEFAULT 0,
    server_id bigint
);


ALTER TABLE public.recruitment OWNER TO postgres;

--
-- Name: terrains; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.terrains (
    id integer,
    name text,
    modifier double precision,
    color text,
    roll integer
);


ALTER TABLE public.terrains OWNER TO postgres;

--
-- Name: trade_goods; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.trade_goods (
    name text,
    market_value integer,
    color text
);


ALTER TABLE public.trade_goods OWNER TO postgres;

--
-- Data for Name: blacklist; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.blacklist (user_id, status, end_time, mod_id, reason, active, action_id, action_date) FROM stdin;
\.


--
-- Data for Name: cnc_data; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.cnc_data (data_name, data_value) FROM stdin;
resources	0
deaths	0
turn	0
\.


--
-- Data for Name: cnc_events; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.cnc_events (name, effects, weight, type, duration, turns) FROM stdin;
Bountiful Harvest	+50% manpower increase	100	national	1	0
Scant Harvest	-50% manpower increase	100	national	1	0
Population Boom	+25% manpower increase	100	national	4	0
Population Decline	-25% manpower increase	100	national	4	0
Disease Outbreak	Flat 25% manpower loss	100	national	0	0
Trade Boom	+1 market value (all goods)	100	national	1	0
Trade Decline	-1 market value (all goods) [to 0.5]	100	national	1	0
Trade Route Closes	Random trade route closes	100	national	0	0
Military Reform	+ 1 to army level	100	national	4	0
Robber Bands	-3 market value for random trade good (to 0.5)	100	national	4	0
Privateers	+2 market value (all goods)	100	national	2	0
Military Mutiny	+25% troop upkeep cost	100	national	4	0
Allied Military Coordination	-15% troop upkeep cost	100	national	4	0
Enemy Military Espionage	+15% troop upkeep cost	100	national	4	0
National Scandal	+10 national Unrest	100	national	0	0
Government Scandal	+20 national Unrest	100	national	0	0
International Scandal	Random alliance ends, +40 national Unrest	100	national	0	0
Social Reform	-10 national Unrest	100	national	0	0
Patriotic Parade	-10 national Unrest, -10% troop upkeep cost	100	national	2	0
Heroic Battle	-15 national Unrest, 5% troop upkeep cost	100	national	1	0
Disastrous Battle	+10 national Unrest	100	national	2	0
Religious Festival	-25 national Unrest	75	national	2	0
Religious Scandal	+25 national Unrest	75	national	2	0
Religious Miracle	-50 national Unrest	25	national	1	0
Religious Disaster	+50 national Unrest	25	national	1	0
Corruption	+20 national Unrest	100	national	2	0
Royal Death	+20 national Unrest	100	national	4	0
Royal Birth	-20 national Unrest	100	national	4	0
Pleased Nobles	-10 national Unrest	100	national	2	0
Unhappy Nobles	+10 national Unrest	100	national	2	0
Noble Endorsement	+15% tax efficiency	100	national	2	0
Religious Endorsement	-15 national Unrest	100	national	2	0
Renowned Scientist Arrives	Reduce research turn by 1	100	national	4	0
Wealthy Merchant Arrives	+1 market value (all goods)	100	national	4	0
Powerful General Arrives	-25% troop upkeep cost	100	national	4	0
Submissive Serfs	+0.5 production efficiency per Workshop	100	national	2	0
Worker Strike	-0.5 production efficiency per Workshop	100	national	2	0
Newly Minted Coins	+5 market value for gold and silver	50	national	4	0
Counterfeit Coinage	-5 market value for gold and silver (to 0.5)	50	national	4	0
New Mine Struck	+5 market value for gold and silver	50	global	8	0
Organized Peasant Uprising	+15 national Unrest	50	global	4	0
Lunar Eclipse	+5% global manpower, -1 market value for random trade good	80	global	2	0
Famine	-25% global manpower	75	global	8	0
Mines Run Dry	-5 market value for gold and silver	50	global	8	0
International Trade Collapse	-5 market value for random trade good	80	global	0	0
Calm And Mild Spring	-5 national Unrest, +5% global manpower	80	global	4	1
Plague	-75% global manpower	25	global	16	0
New Trade Highway	+3 market value for random trade good	80	global	0	0
Bountiful Autumn	+25% global manpower	80	global	4	0
Solar Eclipse	+5 national Unrest, -1 market value for random trade good	80	global	2	0
Comet Sighting	+5 national Unrest	80	global	4	0
\.


--
-- Data for Name: cnc_modifiers; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.cnc_modifiers (user_id, wool_mod, fish_mod, fur_mod, grain_mod, livestock_mod, salt_mod, wine_mod, copper_mod, iron_mod, precious_goods_mod, spices_mod, tea_and_coffee_mod, chocolate_mod, cotton_mod, sugar_mod, tobacco_mod, dyes_mod, silk_mod, rare_wood_mod, glass_mod, paper_mod, precious_stones_mod, coal_mod, gold_mod, fruits_mod, raw_stone_mod, wood_mod, silver_mod, tin_mod, ivory_mod, income_mod, tax_mod, workshop_production_mod, production_mod, trade_route, trade_route_efficiency_mod, national_unrest_suppression_efficiency_mod, local_unrest_suppression_efficiency_mod, defense_level, attack_level, army_limit, movement_cost_mod, manpower_mod, troop_upkeep_mod, research_mod) FROM stdin;
293518673417732098	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	1	1	1	1	0	1	1	1	1	1	15000	1	1.05	1	0.9
\.


--
-- Data for Name: cnc_researching; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.cnc_researching (user_id, tech, turns) FROM stdin;
\.


--
-- Data for Name: cnc_tech; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.cnc_tech (name, effect, prerequisites, description, exclusive, field, image, cords) FROM stdin;
Temples	Unlocks Temple	Construction, Religion	A temple is a building reserved for spiritual rituals and activities such as prayer and sacrifice. Temples are places of social gathering, uniting people of the same faith in the same place. 	\N	Strategy	https://www.medieval.eu/wp-content/uploads/Domenico_Quaglio1787-837-the-Cathedral-in-Reims.jpg	(7346,2258)
Basic Metalworking	+20000 army cap	None	Metalworking is the process of shaping and reshaping metals to create useful objects, parts, assemblies, and large scale structures. Basic metalworking involves shaping copper or another such soft metal into useful shapes and tools. 	\N	Military	http://cdn.shopify.com/s/files/1/0073/5877/5399/articles/History-blacksmithing_1200x1200.JPG?v=1574191989	(4376,432)
Currency	+5% tax efficiency	None	Currency is the standardization of money in any form, in use or circulation as a medium of exchange, for example banknotes and coins. Currencies allow for the exchange of value and worth in a light and transportable method. This method of transporting value facilitates trade and commerce. 	\N	Economy	https://st2.depositphotos.com/3352229/9711/i/950/depositphotos_97115380-stock-photo-hoard-of-medieval-gold-coins.jpg	(2266,432)
Writing	+5% research speed	None	Writing is a medium of human communication that involves the representation of a language through a system of physically inscribed symbols. Early writing is usually inscribed on stone, clay, or wood. Later developments used brushes or pens combined with ink to mark paper, papyrus, or parchment.	\N	Strategy	https://media.istockphoto.com/illustrations/solon-lawmaker-in-ancient-athens-wood-engraving-published-1880-illustration-id686344418?k=20&m=686344418&s=612x612&w=0&h=3e94yQD7LAz9hJJAcrpJAiIz1d0bFTrNxC5oSYFpvRo=	(6515,432)
Agriculture	+1 market value for grain, wine, tea/coffee, sugar, tobacco, and fruits	Currency	Agriculture or farming is the practice of cultivating plants and livestock. Agriculture is the key development in the rise of sedentary human civilization, whereby farming of domesticated species created food surpluses that enabled people to live in cities.	\N	Economy	https://i.pinimg.com/originals/79/1e/4a/791e4abee9a5f3af64be0ba92f2a1f49.png	(2752,905)
Local Trade	+0.5% income per province	Currency	Trade involves the transfer of goods and services from one person or entity to another, often in exchange for money. An early form of trade, the Gift economy, saw the exchange of goods and services without an explicit agreement for immediate or future rewards. A gift economy involves trading things without the use of money. This allows for the advent of small, local economies to form and generate wealth.	\N	Economy	https://www.1st-art-gallery.com/thumbnail/200000/200352/painting_page_800x/Robertson/Carpet-Bazaar,-Cairo,-1887.jpg?ts=1505655060	(1780,905)
Literacy 	+5% research speed	Writing	Literacy describes particular ways of thinking about and doing reading and writing with the purpose of understanding or expressing thoughts or ideas in written form in some specific context of use. Literacy allows for the long-distance or long-lasting exchange and study of ideas. 	\N	Strategy	https://www.historytoday.com/sites/default/files/articles/medievalschool.jpg	(7001,1377)
Philosophy	+5% national unrest suppression efficiency	Literacy	Philosophy is the systematized study of general and fundamental questions, such as those about existence, reason, knowledge, values, mind, and language. Philosophy is the basis for the study of the world, sciences, and theology. 	\N	Strategy	https://brewminate.com/wp-content/uploads/2017/09/090617-11-Presocratic-Philosophy.jpg	(7690,1377)
Dockyards	Unlocks Ports	Navigation, Construction, Local Trade	A port is a maritime facility comprising one or more wharves or loading areas, where ships load and discharge cargo and passengers. Ports and dockyards are crucial for the building and launching of ships, as well as conducting trade and commerce. 	\N	Strategy	https://cdna.artstation.com/p/assets/images/images/037/947/550/4k/s-leon-n-1.jpg?1621763526	(6515,2258)
Construction	-5% building cost	Literacy	Construction is the act of building or assembling a structure. Early construction consisted of using wood or rocks to create huts and storage buildings. Later construction efforts include using bricks, mortar, and carved stone. 	\N	Strategy	https://medievalbritain.com/wp-content/uploads/2021/01/medieval-job-occupations_stone-carver.jpg	(7001,1828)
Comitati	+1 army defense level	Early Armor	Precursors to knights, comitati are glorified berserkers. Carrying heavy weapons and riding a horse, these fearsome soldiers acted as the shock troops for any lord's retinue. 	\N	Military	https://i.pinimg.com/736x/d7/1d/d5/d71dd5e2d4e980ad8c006488444154a6.jpg	(3890,2709)
Navigation	-25% movement cost across water	Sailing	Navigation is a field of study that focuses on the process of monitoring and controlling the movement of a craft from one place to another, especially sailing vessels. The earliest navigation was based on computing distance from two land points, but navigation now relies on the stars, planets, and time. Navigation allows for ships to leave the sight of land and navigate across long distances with relative accuracy.	\N	Strategy	https://images.fineartamerica.com/images-medium-large/armillary-sphere-18th-century-artwork-detlev-van-ravenswaay.jpg	(6029,1828)
Horsemanship	-25% movement cost	Trained Soldiers	Cavalry are soldiers or warriors who fight mounted on horseback. Cavalry are the most mobile of the combat arms, operating as light cavalry in the roles of reconnaissance, screening, and skirmishing in many armies, or as heavy cavalry for decisive shock attacks in other armies. 	\N	Military	https://cdn.shopify.com/s/files/1/0969/9128/products/AdolfSchreyer-ArabianHorsemen_7b3e5fb0-c9c6-41aa-8e88-f9b662331357.jpg?v=1630480127	(3890,1377)
Early Armor	+1 army defense level	Iron Metalworking	Armor is a covering used to protect an individual from physical injury or damage, especially direct contact weapons or projectiles during combat. Early forms of armor were crafted from leather or bamboo, but expanded to include iron mail and lamellar. 	\N	Military	https://www.sword-buyers-guide.com/images/xia-in-battle.jpg	(3890,2301)
Gunpowder	+1 army attack level, +20% Destruction succeed chance	Heraldry, Early Industrialization, Chemistry	Gunpowder, also commonly known as black powder, is the earliest known chemical explosive. Early uses were limited to fireworks and fire-lances, but quickly developed into early forms of the gun, with the cannon and the arquebus. These, when applied to the battlefield, changed warfare forever. 	Levee En Masse	Military	https://www.studio88.co.uk/acatalog/detail_gic_g112_tewkesbury_melee.jpg	(3694,5974)
Munitions Armor	+50000 army cap	Levee En Masse	Munition armour is mass-produced armour stockpiled in armouries to equip both foot soldiers and mounted cuirassiers. The lightweight, cheap armor allows for the raising and maintaining of standing armies equipped with mass-produced weapons.\r\n	Light Infantry	Military	https://qph.cf2.quoracdn.net/main-qimg-d20714f1d7bdec867df7a4bc9f23c3ca-lq	(4748,6409)
Mathematics	+5% research speed	Writing	Mathematics is an area of knowledge that includes such topics as numbers, formulas and related structures, shapes and the spaces in which they are contained, and quantities and their changes. Mathematics allows for the understanding of complex ideas and engineering, as well as sciences, medicine, finance, and architecture.	\N	Strategy	http://www.famousmathematicians.net/photos/pythagoras.jpg	(6515,883)
Livestock Farming	+1 market value for wool, fur, livestock, and fish	Animal Husbandry	Livestock are the domesticated animals raised in an agricultural setting to provide labor and produce commodities such as meat, eggs, milk, fur, leather, and wool. Large scale livestock farming creates a demand and a source for more meat, wool, and fur than was possible to meet before. 	\N	Strategy	https://uploads3.wikiart.org/images/charles-cottet/selling-livestock.jpg!Large.jpg	(8370,1828)
Cash Crops	+1 market value for tobacco, sugar, cotton, and tea/coffee	Crop Rotation	A cash crop or profit crop is an agricultural crop which is grown to sell for profit. It is typically purchased by parties separate from a farm. The term is used to differentiate marketed crops from staple crop in subsistence agriculture, which are those fed to the producer's own livestock or grown as food for the producer's family. These cash crops include, primarily, the planting of tobacco, coffee, tea, cotton, or sugarcane. 	\N	Strategy	https://render.fineartamerica.com/images/images-profile-flow/400/images/artworkimages/mediumlarge/1/limestone-county-cotton-carole-foret.jpg	(9342,1828)
Crop Rotation	+1 market value for grain, wine, tea/coffee, sugar, tobacco, and fruits	Irrigation	Crop rotation is the practice of growing a series of different types of crops in the same area across a sequence of growing seasons. It reduces reliance on one set of nutrients, pest and weed pressure, and the probability of developing resistant pests and weeds. 	\N	Strategy	https://upload.wikimedia.org/wikipedia/commons/d/d2/Medieval-farming.jpg	(9342,1377)
Irrigation	+1 market value for grain, wine, tea/coffee, sugar, tobacco, and fruits	Mathematics	Irrigation is the agricultural process of applying controlled amounts of water to land to assist in the production of crops, as well as to grow landscape plants and lawns, where it may be known as watering. Irrigation helps to grow agricultural crops, maintain landscapes, and revegetate disturbed soils in dry areas and during periods of less than average rainfall. Irrigation also has other uses in crop production, including frost protection, suppressing weed growth in grain fields, and preventing soil consolidation.	\N	Strategy	https://www.timelessmyths.com/wp-content/uploads/2021/10/mesopotamian-irrigation-system.jpg	(8856,883)
Early Industrial Farming	+1 market value for grain, wine, tea/coffee, sugar, tobacco, fruits, wool, fur, livestock, and fish	Cash crops	Industrial agriculture is a form of farming that refers to the industrialized production of crops and animals and animal products like eggs or milk. Early industrial farming is a relatively efficient method of herding animals in large amounts or using equippment and labor to produce larger amounts of crop yield. 	\N	Strategy	https://smarthistory.org/wp-content/uploads/2021/12/N-1207-00-000049-wpu.jpg	(8856,2258)
Religion	+5% national unrest suppression efficiency	Philosophy	Religion is a social-cultural system of designated behaviors and practices, morals, beliefs, worldviews, texts, sanctified places, prophecies, ethics, or organizations, that generally relates humanity to supernatural, transcendental, and spiritual elements. Religion is a crucial pillar of many functioning societies, allowing people to believe in something, real or not. 	\N	Strategy	https://www.worldhistory.org/img/r/p/500x600/9659.jpg?v=1649957466	(7690,1828)
Privateering	+1% trade route efficiency per incoming trade route, +5% if at war	Merchants	A privateer is an individual or organization that engages in trade warfare for the purpose of gaining money and goods. Privateers are commissioned by nations with a letter of marque to raid and take ships of the enemy for profit and strategic advantage.	Trade Fleets	Economy	https://www.paintingstar.com/static/gallery/2014/02/05/5548fa6211437.jpg?The+Gallant+Privateer+The+U.s.s.+Rattlesnake+Artwork+by+Montague+Dawson	(1144,3568)
Cottage Industry	+1 production value on all trade goods, excluding gold and silver	Manorialism	A cottage industry is an industry—primarily manufacturing—which includes many producers, working from their homes, and was often organized through the putting-out system. The biggest contributors in this system were the merchant capitalist and the rural worker. The merchant would "put-out" basic materials to the cottage workers, who then prepared the materials in their own homes and returned the finished merchandise back to the merchant.	Early Industrialization	Economy	https://render.fineartamerica.com/images/images-profile-flow/400/images-medium-large-5/medieval-cottage-christian-jegou-publiphoto-diffusion-science-photo-library.jpg	(1780,5093)
Economic Stratification	+5% tax efficiency	Local Trade, Agriculture, Mathematics	Economic stratification is the condition within a society where social classes are separated, or stratified, along economic lines. This allows for the structuring of a society and an economy based on local production and industry.	\N	Economy	https://i.pinimg.com/474x/99/e4/1d/99e41d929d59a41a73b8af7e96f4fb4d.jpg	(2266,1377)
Cuirass	-25% movement cost, +25000 army cap	Gunpowder	A cuirass is a piece of armour that is formed of a single or multiple pieces of metal or other rigid material which covers the torso. The lightness and mobility of this armor allows infantry and cavalry to manuver quickly. Its cheap design also allows for mass deployment.	Gothic Plate	Military	https://fristartmuseum.org/wp-content/uploads/Armor_GiovanneDelleBandeNere_MuseoStibbert.jpg	(4009,6398)
Demi-Lancer	-25% movement cost, +50000 army cap	Chivalry	Demi-lancers are cavalrymen mounted on unarmoured horses, armed with a slightly lighter version of the heavy lance of a man-at-arms and wearing three-quarter or half-armour, in contrast to the full plate armour of the man-at-arms or gendarme. This abbreviated armour is meant to increase the mobility of the men and horses, as well as reducing the expense of equipping and maintaining them throughout a long campaign, allowing them to be an effective flanking and routing force.	Gendarmes	Military	https://upload.wikimedia.org/wikipedia/commons/thumb/2/2d/Carlos_V_en_la_Batalla_de_M%C3%BChlberg%2C_por_Tiziano.jpg/220px-Carlos_V_en_la_Batalla_de_M%C3%BChlberg%2C_por_Tiziano.jpg	(3890,5093)
Levee En Masse	+ 100000 army cap	Heraldry, Printing Press	The term levée en masse denotes a short-term requisition of all able-bodied men to defend the nation, especially when faced with a general invasion. This allowed armies to bolster their numbers by conscripting able-bodied men to a term of service, sometimes required of all citizens. 	Gunpowder	Military	https://i.pinimg.com/originals/6f/f3/9e/6ff39e158cd86361079a1fa3cab3e385.jpg	(5050,5974)
Trade Regulations	+1% trade route efficienty per incoming and outgoing trade routes	Trading Ports or Predatory Training, Regional Governance	Trade regulations allow for the protection and benefit of merchants and international trade. These regulations are agreed-upon treaties signed by member nations in an effort to allow for the free and profitable movement of goods and services. These treaties may be global in effect or designed to benefit small groups of like-minded nations. 	\N	Economy	https://i.guim.co.uk/img/media/3de29877b87155507b3364e32134abd9f17a34d5/66_73_5838_4123/2000.jpg?width=620&quality=85&auto=format&fit=max&s=ed58ded377d1dc6e59ad8e2654129c65	(658,4492)
Predatory Trading	+1% trade route efficienty per incoming trade route	Privateering	Predatory trade practices enable a nation to price its goods in such a way that benefits themselves and harms foreign merchants. Striking a balance between cost and lost is an important part of predatory trading.	\N	Economy	https://ae01.alicdn.com/kf/HTB1Gwp3KFXXXXaUXpXXq6xXFXXX9/Pirate-Ship-Attack-Sea-Battle-Ocean-Large-Oil-Painting.jpg_Q90.jpg_.webp	(1144,4019)
Trading Ports	+1% trade route efficiency per port	Trade Fleets	A port is a maritime facility comprising one or more wharves or loading areas, where ships load and discharge cargo and passengers. Trading ports are havens for the loading and unloading of cargo, the purchasing of merchandise and goods, and the establishment of trade routes. 	\N	Economy	https://worldhistoryconnected.press.uillinois.edu/13.1/images/maunu_fig02b.jpg	(172,4019)
Heraldry	+25% suppression efficiency	Gendarmes/Demi-Lancer	Heraldry is a discipline relating to the design, display and study of armorial bearings, as well as related disciplines, such as vexillology, together with the study of ceremony, rank and pedigree. Heralds are tasked with the memorization and protection of noble coats of arms, ensuring that all know and respect their noblemen. 	\N	Military	https://upload.wikimedia.org/wikipedia/commons/thumb/1/1b/Hyghalmen_Roll_Late_1400s.jpg/640px-Hyghalmen_Roll_Late_1400s.jpg	(4376,5544)
Iron Metalworking	+50000 army cap	Horsemanship, Archery	Metalworking is the process of shaping and reshaping metals to create useful objects, parts, assemblies, and large scale structures. Higher temperatures achieved in forges and the advent of deeper mining allows for the emergence of ironworking as a craft. Iron is stronger than copper or gold, allowing it to be an effective replacement for weapons, tools, and armor.  	\N	Military	https://i.pinimg.com/originals/53/84/c2/5384c2c4423cbc4a59cd5bca7c2d955d.jpg	(4376,1850)
Fortifications	Unlocks forts	Military Strategy, Construction	A fortification is a military construction or building designed for the defense of territories in warfare, and is also used to establish rule in a region during peacetime. The first forts were nothing more than earthworks and wooden palisades, but eventually evolved into massive castles and strong keeps. 	\N	Military	https://www.northwindprints.com/p/473/medieval-castle-5880535.jpg	(4862,3139)
Gendarmes	+1 army attack level, +1 army defense level	Chivalry	Gendarmes are plate-ensconsed warriors riding on armored horses in small companies capable of enflicting powerful strikes at the enemy. Called up from the countryside, these soldiers also help to keep the local peace and helped with the enforcement of the local governor's demands. 	Demi-Lancer	Military	https://upload.wikimedia.org/wikipedia/commons/3/3e/1518_Altdorfer_Sieg_Karls_des_Grossen_ueber_die_Awaren_anagoria_%28cropped%29.JPG	(4862,5093)
Light Infantry	-25% movement cost	Levee En Masse	Light infantry is a designation applied to certain types of foot soldiers (infantry), typically having lighter equipment or armament or a more mobile or fluid function than other types of infantry. Light infantry, including skermishers and scouts, act as a harassing force on the enemy, scouting ahead, ambushing supply lines, and attacking flanks. Light infantry are also necessary for screening, which increases the ability of a larger force to move undetected with speed. 	Munitions Armor	Military	https://static.wikia.nocookie.net/gotmp/images/0/0f/3490_8ce0_960.png/revision/latest?cb=20160120212101	(5352,6409)
Local Tariffs	+0.5% production per province	Guilds	A tariff is a tax imposed by the government of a country or city on imports or exports of goods. Besides being a source of revenue for the government, import duties can also be a form of regulation of foreign trade and policy that taxes foreign products to encourage or safeguard domestic industry. Tariffs are among the most widely used instruments of protectionism, along with import and export quotas.	\N	Economy	https://render.fineartamerica.com/images/rendered/square-dynamic/small/images-medium-large-5/la-demoiselle-de-coucy-an-attendant-mary-evans-picture-library.jpg	(1780,4041)
Guilds	+0.5 production per Workshop	Cities	A guild is an association of artisans and merchants who oversee the practice of their craft or trade in a particular area. The earliest types of guild formed as organizations of tradesmen belonging to a professional association. They sometimes depended on grants of letters patent from a monarch or other ruler to enforce the flow of trade to their self-employed members, and to retain ownership of tools and the supply of materials, but were mostly regulated by the city government. Guild members found guilty of cheating the public would be fined or banned from the guild.	\N	Economy	http://www.metmuseum.org/-/media/images/blogs/now-at-the-met/2015/2015_08/grace-under-pressure/1.jpg?sc_lang=en	(1780,3590)
Cities	Unlocks City building	International Trade, Early Industry, Animal Husbandry	A city is a large, permanent, and densely settled place with administratively defined boundaries whose members work primarily on non-agricultural tasks. Cities generally have extensive systems for housing, transportation, sanitation, utilities, land use, production of goods, and communication. Their density facilitates interaction between people, government organizations, and businesses, sometimes benefiting different parties in the process, such as improving efficiency of goods and service distribution. 	\N	Economy	https://i.pinimg.com/originals/98/94/9f/98949f4b1d855ca9726ee6d8fa8df7f9.png	(2266,3139)
Trained Soldiers	+1 army atack level	Basic Metalworking	A soldier is a person who is a member of an army. A soldier can be a conscripted or volunteer enlisted person, a non-commissioned officer, or an officer. Trained soldiers allow for the proper use and application of military force against enemies of the state.	\N	Military	https://media.istockphoto.com/illustrations/ancient-roman-legionary-armed-with-spear-and-shields-illustration-id1031932994?k=20&m=1031932994&s=612x612&w=0&h=KwCSZNlh80gdBKuv25t-VB75kptMdqG_BcxKXiGN-oo=	(4376,883)
Siege Engines	Unlocks Destruction tactic, +20% chance to succeed 	Steel Metalworking, Engineering	A siege engine is a device that is designed to break or circumvent heavy castle doors, thick city walls and other fortifications in siege warfare. Some are immobile, constructed in place to attack enemy fortifications from a distance, while others have wheels to enable advancing up to the enemy fortification. There are many distinct types, such as siege towers that allow foot soldiers to scale walls and attack the defenders, battering rams that damage walls or gates, and large ranged weapons (such as ballistae, catapults/trebuchets and other similar constructions) that attack from a distance by launching projectiles.	\N	Military	https://images.fineartamerica.com/images/artworkimages/mediumlarge/1/a-medieval-catapult-from-sveriges-ken-welsh.jpg	(4862,4041)
Archery	+1 army attack level	Trained Soldiers	Archers are some of the oldest and most powerful of trained soldiers. Their ability to quickly move and strike from afar make them a crucial tool in the execution of any war. 	\N	Military	https://archeryhistorian.com/wp-content/uploads/2018/11/Ain-Jalut-tapestry.jpg	(4862,1377)
Retinues	+1 army attack level	Comitati	A retinue is a body of persons retained in the service of a noble, royal personage, or dignitary. Military retinues act as permanent, well-trained soldiers that make up the core of an army. They are expensive to maintain, but are highly trained and focused. 	\N	Military	https://brewminate.com/wp-content/uploads/2020/07/072620-12-History-Medieval-Middle-Ages-Russia.jpg	(3890,3139)
Professional Soldiers	+1 army attack level	Iron Metalworking	A soldier is a person who is a member of an army. A soldier can be a conscripted or volunteer enlisted person, a non-commissioned officer, or an officer. Professional soldiers are highly-practiced and paid soldiers that are relatively expert at their craft. 	\N	Military	https://www.medievalchronicles.com/wp-content/uploads/2015/10/Medieval-Warfare-Battles-Batalla-de-rocroi-por-Augusto-Ferrer-Dalmau.jpg	(4862,2301)
Military Strategy	+1 army attack level	Professional Soldiers, Literacy	Military strategy is a set of ideas implemented by military organizations to pursue desired strategic goals. Discovering, creating, and implimenting military strategy is an important step to getting an edge over the enemy. Military strategy allows for generals and leaders to deploy and order their troops with precision and efficiency. 	\N	Military	http://deremilitari.org/wp-content/uploads/2014/05/cf650ac3f1d2fc01e94ad438b68986c2.jpg	(4862,2709)
International Trade	Unlocks Trade Routes	Regional Trade, Navigation	Trade involves the transfer of goods and services from one person or entity to another, often in exchange for money. After the development of regional trade, merchants and traders established trade routes that spanned across vast areas of land, regardless of national border. The establishment of trade route treaties protecting merchants on the road allowed for the facilitation of international trade routes. 	\N	Economy	https://i.pinimg.com/736x/32/03/07/3203077419396ec8972e953ed8fcf1fd.jpg	(1780,2301)
Education	+5% research speed	Temples	Education is a purposeful activity directed at achieving certain aims, such as transmitting knowledge or fostering skills and character traits. These aims may include the development of understanding, rationality, kindness, and honesty, usually though the emphasis of critical thinking. Education is a important component of building a society. 	\N	Strategy	https://kajabi-storefronts-production.kajabi-cdn.com/kajabi-storefronts-production/themes/2318725/settings_images/r7TIlTrPS0qQWj76ZXx6_pasted_image_0_11.png	(7346,2709)
City Administration	+1% tax efficiency	Education	Cities, administered by local officials, are a pillar of every society, not only for their economical importance, but also their cultural importance. Focusing on efficient city administration will increase the effectiveness of local officals and tax collectors. 	\N	Strategy	https://home.uchicago.edu/~rfulton/Buda.jpg	(8652,2709)
National Government	+5% national unrest suppression efficiency	Regional Governance	National governments are the centralized government in control over the nation as a whole. National governments, monarchies or otherwise, must administer their nation with an iron fist or a gentle hand. 	\N	Strategy	https://upload.wikimedia.org/wikipedia/commons/b/bf/Charles-vii-courronement-_Panth%C3%A9on_III.jpg	(8652,3590)
Animal Husbandry	+1 market value for wool, fur, livestock, and fish	Irrigation	Animal husbandry is the branch of agriculture concerned with animals that are raised for meat, fibre, milk, or other products. It includes day-to-day care, selective breeding, and the raising of livestock. 	\N	Strategy	data:image/jpeg;base64,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	(8370,1377)
Early Industry	+0.5 production per Workshop	Workshops	Having established the ability to quickly produce materials and goods, early industries provided cultures with the ability to create booming economic growth and centralized wealth.	\N	Economy	https://www.northwindprints.com/p/473/medieval-goldsmith-work-5879350.jpg	(2752,2301)
Economics	+0.5% tax efficiency	Global Markets	Economics focuses on the behaviour and interactions of economic agents and how economies work. The study of economics allows for nations and markets to make the most efficient use of their available resouces.	\N	Economy	https://voxeu.org/sites/default/files/image/FromAug2010/EtroFig1a.gif	(2752,4041)
Workshops	Unlocks Workshop building	Economic Stratification	Workshops were the only places of production until the advent of industrialization and the development of larger factories. These buildings allow for the production of materials and finished goods on a scale previously impossible. 	\N	Economy	https://pbs.twimg.com/media/EID8aVyWkAAo_Kv.jpg	(2752,1850)
Regional Trade	+1% income per province	Economic Stratification	Trade involves the transfer of goods and services from one person or entity to another, often in exchange for money. Having developed the basis for a trade economy locally, individuals and early businesses began traveling to more distant locations to sell and trade, creating a larger economic range.	\N	Economy	https://mythicscribes.com/wp-content/uploads/2017/12/wagon-sketch.jpg	(1780,1850)
Printing Press	+5% national unrest suppression efficiency	Engineering	A printing press is a mechanical device for applying pressure to an inked surface resting upon a print medium (such as paper or cloth), thereby transferring the ink. It marked a dramatic improvement on earlier printing methods in which the cloth, paper or other medium was brushed or rubbed repeatedly to achieve the transfer of ink, and accelerated the process. This allows for the mass production of written works and publications, especially retaining to government or science. 	\N	Strategy	http://gallica.bnf.fr/iiif/ark:/12148/btv1b84521932/f37/868,1832,724,497/724,497/0/native.jpg	(7832,3590)
Chemistry	+5% research speed	Machines, Printing Press	Chemistry is the scientific study of the properties and behavior of matter, especially their reactions to each other. Chemistry started out as nothing more than attempts at alchemy, but it has evolved into a stronger science that encourages extensive discovery and the exploration of the world. 	\N	Strategy	https://i.imgur.com/ZqXShxv.png	(7346,4041)
Gothic Plate	+1 army defense level	Gunpowder	Gothic plate is a style of full-plate armor that is made of high quality steel, capable of protecting against some small-arms fire and most weapons. This heavy plate is worn only by the richest of the knight class, forming a core of super-heavy cavalry. 	Cuirass	Military	https://upload.wikimedia.org/wikipedia/commons/thumb/8/8c/Gothic_armor_2.jpg/800px-Gothic_armor_2.jpg	(3404,6398)
Machines	+0.5 production per Workshop	Engineering	A machine is a physical system using power to apply forces and control movement to perform an action. The term is commonly applied to artificial devices, such as those used to augment or replace human labor. Windmills, watermills, and other such devices replace the hand-labor of several dozen workers, freeing them up to do more productive things with their time. 	\N	Strategy	http://gallica.bnf.fr/iiif/ark:/12148/btv1b84521932/f37/868,1832,724,497/724,497/0/native.jpg	(6860,3590)
Regional Governance	+1% local unrest suppression efficiency	City Administration	Nations can be divided into smaller areas of land, or regions, which allow for decentralized and more effective governance. Regional officials can be entrusted to represent the will of the current ruler while also voicing the needs of the peasants. 	\N	Strategy	https://images-wixmp-ed30a86b8c4ca887773594c2.wixmp.com/f/ebd5c37b-60a4-4e72-a880-be8d689025f2/de3u1x7-fa5ad29d-e4cb-4fcc-82a8-617636f4f500.jpg/v1/fill/w_696,h_350,q_70,strp/seaside_barony_by_andrewryanart_de3u1x7-350t.jpg?token=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ1cm46YXBwOjdlMGQxODg5ODIyNjQzNzNhNWYwZDQxNWVhMGQyNmUwIiwiaXNzIjoidXJuOmFwcDo3ZTBkMTg4OTgyMjY0MzczYTVmMGQ0MTVlYTBkMjZlMCIsIm9iaiI6W1t7ImhlaWdodCI6Ijw9NTE2IiwicGF0aCI6IlwvZlwvZWJkNWMzN2ItNjBhNC00ZTcyLWE4ODAtYmU4ZDY4OTAyNWYyXC9kZTN1MXg3LWZhNWFkMjlkLWU0Y2ItNGZjYy04MmE4LTYxNzYzNmY0ZjUwMC5qcGciLCJ3aWR0aCI6Ijw9MTAyNCJ9XV0sImF1ZCI6WyJ1cm46c2VydmljZTppbWFnZS5vcGVyYXRpb25zIl19.iICJRp19FX92cmco8TQzSy7u2fx40AliP-deSySKUtM	(8652,3149)
Engineering	-5% construction cost	Education	Engineering is the use of scientific principles to design and build machines, structures, and other items, including bridges, tunnels, roads, vehicles, and buildings. Early engineering focused on the creation of tools and buildings, but now engineering encompasses public works, siege engines, defenses, and urban planning. 	\N	Strategy	https://i.pinimg.com/originals/aa/e5/b0/aae5b0938b3eadb03e385eb1b4fbeaa6.jpg	(7346,3160)
Trade Fleets	+5% trade route efficiency	Merchants	Protection in numbers drives many merchants to combine their forces when traveling to and from trade destinations. Trade fleets allow for merchants to protect their goods and materials from pirates and robbers. 	Privateering	Economy	https://d3d00swyhr67nd.cloudfront.net/w1200h1200/collection/NMM/NMMG/NMM_NMMG_BHC0858-001.jpg	(172,3568)
Sailing	Unlocks water travel	Mathematics	Sailing employs the wind—acting on sails, wingsails or kites—to propel a craft on the surface of the water. Sailing ships are the primary means of maritime trade and transportation, especially trade. 	\N	Strategy	https://p4.wallpaperbetter.com/wallpaper/358/1011/701/art-and-creative-wallpaper-preview.jpg	(6029,1377)
Early Industrialization	+2 production efficiency to all Workshops	Banking and Investments, Machines	Manufacturing is the creation or production of goods with the help of equipment, labor, machines, tools, and chemical or biological processing or formulation. Centralized industry combined with urban demographics creates the demand for mass-produced, low-quality items using machines and low cost labor.	Cottage Industry	Economy	https://1.bp.blogspot.com/-kpFaM-7JO1Q/WKisrCC75VI/AAAAAAAA4Xw/iYXh6Vp6HMsTwgRozuojWqcLsL6Qe9eRQCLcB/s1600/3w-industrial.jpg	(2752,5093)
Banking and Investments	+1 trade route	Economics	A bank is a financial institution that accepts deposits from the public and creates a demand deposit while simultaneously making loans. Lending activities can be directly performed by the bank or indirectly through capital markets. Investment is the dedication of an asset to attain an increase in value over a period of time. Investment requires a sacrifice of some present asset, such as time, money, or effort. Combined, these two concepts govern a large part of the economic stability of the global markets.	\N	Economy	https://img.medievalists.net/wp-content/uploads/2014/09/The-Money-Lenders-001.jpg?format=webp&compress=true&quality=80&w=376&dpr=2.6	(2752,4492)
Global Markets	+0.25 market value for all trade goods, excluding gold and silver	Cities, Dockyards	A market is a composition of systems, institutions, procedures, social relations or infrastructures whereby parties engage in exchange. The global market is the collection of national and international trade markets that interact through trade and policy.	\N	Economy	https://brewminate.com/wp-content/uploads/2019/03/031819-78-History-Medieval-Middle-Ages-Europe-Trade-Commerce.jpeg	(2752,3590)
Merchants	+5% trade route efficiency	International Trade,	A merchant is a person who trades in commodities produced by other people, especially one who trades with foreign countries. Merchants travel from nation to nation, creating and trading on routes.	\N	Economy	https://render.fineartamerica.com/images/images-profile-flow/400/images-medium-large-5/parade-of-the-black-sea-fleet-in-1849-1886-oil-on-canvas-ivan-konstantinovich-aivazovsky.jpg	(658,3139)
Manorialism	+0.5 production per Workshop	Local Tariffs	Manorialism, also known as the manor system or manorial system, is a method of land ownership. Its defining features include a large, sometimes fortified manor house in which the lord of the manor and his dependents lived and administered a rural estate, and a population of labourers who worked the surrounding land to support themselves and the lord. These labourers fulfilled their obligations with labour time or in-kind produce at first, and later by cash payment as commercial activity increased.	\N	Economy	https://cdn.britannica.com/02/115002-050-C91498DA/Peasants-work-gates-town-painting-Breviarium-Grimani.jpg	(1780,4492)
Plate Armor	+1 army defense level	Steel Metalworking	Plate armour is a type of armor made from bronze, iron, or steel plates, culminating in the iconic suit of armour entirely encasing the wearer. Plate armor, while exorbitantly expensive, provided the wearer with a veritable personal fortress on the battlefield. While only the rich and powerful knights could afford this armor, it allowed them to be more effective in crushing the enemy. 	\N	Military	https://images.fineartamerica.com/images/artworkimages/mediumlarge/2/a-medieval-knight-armed-and-mounted-print-collector.jpg	(3890,4041)
Steel Metalworking	+50000 army cap	Early Industry, Retinues, Fortifications	Metalworking is the process of shaping and reshaping metals to create useful objects, parts, assemblies, and large scale structures. Introducing carbon into iron created a new form of metal: steel. Lighter, more flexible, and able to withstand immense pressures, steel made the creation of heavy armor and weapons feasible. 	\N	Military	https://media.mutualart.com/Images/2011_04/03/08/081801772/67f35389-91c0-4ffc-82bf-9bc8b76991d7_338.Jpeg	(4376,3590)
Chivalry	+1 army attack level	Plate Armor, Siege Engines	Knights are heavily armed, heavily armored horsemen who are highly trained in the art of warfare. Often members of the noble class, knights play both a military and religious role in many nations, following a code of chivalry. During war, knights act as shock troops and commanders, leading vital campaigns against the enemy. 	\N	Military	https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTK1wx94SYewxXT10IuReN47ID9CDdcKAbQRA&usqp=CAU	(4376,4470)
\.


--
-- Data for Name: cncusers; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.cncusers (user_id, username, usercolor, resources, focus, undeployed, moves, manpower, maxmanpower, taxation, military_upkeep, public_services, national_unrest, capital, event, great_power, great_power_score, capital_move, researched, event_duration, trade_route_limit, citylimit, portlimit, fortlimit) FROM stdin;
\.


--
-- Data for Name: currency; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.currency (name, worth, userid, symbol, backed, server_id, nation) FROM stdin;
Oachatl	2.3	552224320257130496	Ø	Gold	674259612580446230	
Shrill	0.2	589496981450260530	₮	Bronze	674259612580446230	
Pangrik	2.1	905858887926816768	₱	Silver	674259612580446230	
Riya	0.7	275497677481836545	Ԙ	Silver	674259612580446230	
Vumeirein	3	765257407064047638	₪	Silver	674259612580446230	
legostuds	5.7	899852149360566323	£	Gold	674259612580446230	
Ihbachks	4.3	965727531263201300	ʊ	Gold	674259612580446230	
Felix	6.32	531430986010066957	F	Gold	674259612580446230	
Rach	5.8	672134523173076995	Ⱒ	Gold	674259612580446230	
Karima	4.3	293518673417732098	λ	Silver	674259612580446230	Bassiliya
Cash	0.05	285855888336486400	¢	Silver	674259612580446230	Shijeun
Almaark	10	235228478088151041	º	nothing	674259612580446230	Almaaz
Libit	0.112	293518673417732098	Ł	gold	549506142678548490	Jaedonstan
koro	6	428949783919460363	₭	Gold	674259612580446230	Nokoroth
Mognus	3.1	844640695868194927	ඞ	Gold	674259612580446230	Cisalpine
\.


--
-- Data for Name: interactions; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.interactions (id, type, sender, sender_id, recipient, recipient_id, terms, active) FROM stdin;
\.


--
-- Data for Name: maxcas; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.maxcas (modifier, "1", "2", "3", "4", "5", "6") FROM stdin;
0	0.05	0.1	0.15	0.25	0.4	0.5
0.05	0.1	0.2	0.3	0.4	0.5	0.6
0.1	0.15	0.25	0.45	0.6	0.65	0.75
0.5	0.5	0.55	0.6	0.75	0.8	0.8
\.


--
-- Data for Name: mod_logs; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.mod_logs (action, reason, mod_id, id) FROM stdin;
\.


--
-- Data for Name: pending_interactions; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.pending_interactions (id, type, sender, sender_id, recipient, recipient_id, terms) FROM stdin;
\.


--
-- Data for Name: provinces; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.provinces (id, terrain, bordering, owner, owner_id, troops, coast, cord, river, value, port, fort, city, manpower, name, unrest, event, uprising, occupier, occupier_id, workshop, temple, production) FROM stdin;
53	0	{23,25,27,49,52,54}		0	310	f	(745,1084)	f	Livestock	f	f	f	4657	Athyastoroklis	0	0	f		0	f	f	1
787	2	{786,788,789}		0	383	t	(3218,39)	f	Salt	f	f	f	3847	Seva	0	0	f		0	f	f	4
1080	7	{1067,1068,1079,1081,1082,1118,1119}		0	114	t	(3252,2030)	f	Fish	f	f	f	292	Kezubenu	0	0	f		0	f	f	3
244	0	{239,240,243,245,246,247}		0	387	f	(1224,722)	t	Cotton	f	f	f	3135	Napby	0	0	f		0	f	f	2
179	0	{155,156,157,158,180,235}		0	251	f	(1345,589)	f	Cotton	f	f	f	3018	Djacahdet	0	0	f		0	f	f	1
20	0	{18,19,21}		0	273	f	(718,1208)	t	Wood	f	f	f	4464	Sepsai	0	0	f		0	f	f	3
395	5	{396,411,412}		0	1164	f	(1638,821)	f	Raw Stone	f	f	f	630	Kisrimeru	0	0	f		0	f	f	2
502	5	{488,500,501,503,506}		0	1026	f	(1249,1314)	f	Silver	f	f	f	838	Sapoyut	0	0	f		0	f	f	2
467	0	{468,471}		0	303	t	(1287,1420)	t	Paper	f	f	f	4185	Tarnouru	0	0	f		0	f	f	1
460	2	{458,459,461}		0	325	t	(1775,817)	f	Livestock	f	f	f	3457	Sasotaten	0	0	f		0	f	f	1
492	5	{472,491,493,494,496}		0	1256	f	(1197,1348)	f	Raw Stone	f	f	f	637	Bema	0	0	f		0	f	f	2
590	2	{558,560,573,588,589,591,592,608}		0	365	f	(1042,2522)	f	Fur	f	f	f	3968	Gesso	0	0	f		0	f	f	1
213	2	{208,209,210,212,214,216,217}		0	308	f	(1080,416)	f	Wine	f	f	f	3751	Shari	0	0	f		0	f	f	2
159	0	{158,160,161,174,175,178}		0	373	f	(1415,578)	f	Wood	f	f	f	3187	Acne	0	0	f		0	f	f	3
1104	5	{1102,1103,1105,1106,1107}		0	1130	f	(3112,1821)	f	Tin	f	f	f	781	Menrusiris	0	0	f		0	f	f	1
114	7	{112,113,120,119}		0	153	f	(731,646)	f	Paper	f	f	f	296	Shapo	0	0	f		0	f	f	1
186	9	{185,187,195,221}		0	166	t	(1300,367)	f	Ivory	f	f	f	237	Senebenu	0	0	f		0	f	f	3
784	2	{780,783,785}		0	371	t	(3099,53)	f	Glass	f	f	f	3528	Tabe	0	0	f		0	f	f	1
317	9	{316,318,319,321,322}		0	129	f	(1705,391)	f	Fur	f	f	f	240	Behbu	0	0	f		0	f	f	1
369	1	{266,289,368,383,370,484}		0	121	f	(1388,972)	f	Paper	f	f	f	598	Dessasiris	0	0	f		0	f	f	3
394	5	{392,393,414}		0	1267	f	(1609,821)	f	Iron	f	f	f	639	Sepdjesut	0	0	f		0	f	f	3
150	2	{149,151,248,295}		0	308	f	(1264,893)	f	Tobacco	f	f	f	2586	Tjendepet	0	0	f		0	f	f	2
782	2	{779,780,781,783}		0	388	t	(3045,49)	f	Livestock	f	f	f	2732	Cupo	0	0	f		0	f	f	2
162	0	{160,161,163,176,300}		0	310	f	(1507,495)	t	Cotton	f	f	f	4488	Wasbumunein	0	0	f		0	f	f	1
694	5	{687,688,689,692,693,695,696}		0	1241	f	(2839,729)	f	Precious Stones	f	f	f	698	Kerdjerma	0	0	f		0	f	f	3
810	2	{802,803,804,809,811,814,815}		0	325	f	(3314,133)	f	Grain	f	f	f	3011	Khemabesheh	0	0	f		0	f	f	4
1208	2	{1207}		0	334	t	(3373,2977)	f	Tin	f	f	f	3714	Kenupis	0	0	f		0	f	f	2
753	2	{747,748,749,752,754,758,759}		0	394	f	(3251,211)	f	Salt	f	f	f	2933	Boroupoli	0	0	f		0	f	f	2
934	0	{931,933,935,936,937,938,939}		0	271	f	(2677,1384)	t	Grain	f	f	f	4755	Epione	0	0	f		0	f	f	4
4	0	{2,3,5,6,7}		0	274	t	(859,1354)	f	Wood	f	f	f	3350	Pelyma	0	0	f		0	f	f	2
858	9	{855,857,859}		0	127	t	(3679,117)	f	Fur	f	f	f	288	Golgona	0	0	f		0	f	f	2
929	0	{928,930}		0	325	t	(2871,1253)	f	Grain	f	f	f	3655	Thebekion	0	0	f		0	f	f	1
596	0	{535,536,552,553,595,597}		0	285	f	(1125,2243)	f	Glass	f	f	f	3421	Juktorus	0	0	f		0	f	f	4
183	2	{177,181,182,222,223,184}		0	384	f	(1370,454)	t	Copper	f	f	f	2815	Phanipolis	0	0	f		0	f	f	4
862	2	{857,859,861,863}		0	303	t	(3683,220)	f	Paper	f	f	f	3439	Tyraphos	0	0	f		0	f	f	2
201	9	{197,198,199,200,202,211}		0	188	t	(1161,272)	f	Fur	f	f	f	234	Pavlosse	0	0	f		0	f	f	1
347	5	{331,345,346}		0	1056	f	(1910,475)	f	Iron	f	f	f	742	Eubacus	0	0	f		0	f	f	2
1047	2	{1043,1044,1041,1042,1046,1048,1049,1050}		0	395	f	(3598,1746)	t	Tobacco	f	f	f	2547	Rhodyrgos	0	0	f		0	f	f	2
277	7	{232,241,276,278,279,281,281}		0	147	t	(1093,594)	f	Silk	f	f	f	171	Myrolgi	0	0	f		0	f	f	1
196	9	{192,193,197,197}		0	160	t	(1210,250)	f	Fish	f	f	f	189	Setrias	0	0	f		0	f	f	2
598	0	{533,534,535,597,599}		0	355	f	(1026,2259)	t	Tea and Coffee	f	f	f	4313	Massipolis	0	0	f		0	f	f	3
811	2	{802,810,812,813,814}		0	351	t	(3312,106)	f	Rare Wood	f	f	f	3498	Corcyreum	0	0	f		0	f	f	4
797	9	{796,798,799}		0	147	t	(3660,48)	f	Glass	f	f	f	223	Megarina	0	0	f		0	f	f	3
903	0	{893,894,895,902,904}		0	344	f	(3901,544)	t	Wool	f	f	f	4654	Laodigona	0	0	f		0	f	f	1
960	0	{944,959,961,1094,1095,1096,1097}		0	253	f	(3042,1519)	t	Wool	f	f	f	4101	Posane	0	0	f		0	f	f	2
310	0	{305,306,309,311,312,429}		0	365	f	(1681,625)	f	Rare Wood	f	f	f	3011	Panteselis	0	0	f		0	f	f	3
644	2	{643,645,648}		0	319	t	(2675,342)	f	Fish	f	f	f	2900	Arsaistos	0	0	f		0	f	f	1
1092	0	{963,964,965,1090,1091,1093}		0	278	f	(3276,1499)	f	Wool	f	f	f	3162	Rhegenes	0	0	f		0	f	f	2
761	0	{0}		0	310	t	(3482,268)	f	Fur	f	f	f	4744	Abymna	0	0	f		0	f	f	4
1129	0	{1128,1130,1131,1143}		0	367	t	(2837,1796)	f	Glass	f	f	f	3970	Lampsens	0	0	f		0	f	f	1
6	0	{4,5,7,8,9}		0	308	t	(916,1318)	f	Fruits	f	f	f	3258	Benion	0	0	f		0	f	f	1
728	0	{668,670,671,724,727,729,730}		0	323	f	(3053,450)	t	Wool	f	f	f	4477	Golgarae	0	0	f		0	f	f	1
1009	0	{1002,1008,1010,1035,1044,1045}		0	268	f	(3573,1519)	t	Livestock	f	f	f	4844	Aytippia	0	0	f		0	f	f	3
313	2	{312,314,332,431}		0	327	f	(1721,475)	f	Glass	f	f	f	2871	Thespeucia	0	0	f		0	f	f	2
769	0	{768}		0	342	t	(3552,516)	f	Grain	f	f	f	4798	Tarre	0	0	f		0	f	f	1
710	2	{702,703,709,711,712}		0	320	f	(2720,855)	t	Copper	f	f	f	4003	Khepeset	0	0	f		0	f	f	3
830	5	{823,829,831}		0	1190	t	(3431,119)	f	Raw Stone	f	f	f	842	Nemtadjed	0	0	f		0	f	f	2
545	1	{541,542,543,544,546,647}		0	103	t	(1510,2376)	f	Glass	f	f	f	516	Behzum	0	0	f		0	f	f	1
731	2	{726,730,732}		0	364	f	(3220,416)	t	Spices	f	f	f	2714	Cythene	0	0	f		0	f	f	3
992	0	{991,993,994,995,996,997}		0	388	t	(3782,1249)	f	Ivory	f	f	f	4609	Agrinaclea	0	0	f		0	f	f	1
994	0	{992,993,995}		0	320	t	(3820,1204)	f	Fish	f	f	f	3764	Zuivild	0	0	f		0	f	f	1
582	1	{581,583,584}		0	151	t	(785,2761)	f	Spices	f	f	f	580	Thisruil	0	0	f		0	f	f	2
1167	0	{1162,1164,1165,1168,1171,1180,1181,1182}		0	287	f	(2831,2390)	f	Fur	f	f	f	4598	Ilvynyln	0	0	f		0	f	f	1
75	2	{74,76,79,80,94,98}		0	375	f	(508,893)	t	Livestock	f	f	f	3404	Teapost	0	0	f		0	f	f	1
786	2	{785,787}		0	386	t	(3176,27)	f	Glass	f	f	f	3491	Starmore	0	0	f		0	f	f	1
800	2	{752,759,801,803,804}		0	338	f	(3260,153)	f	Grain	f	f	f	2809	Strawshire	0	0	f		0	f	f	2
91	2	{87,90,92}		0	357	t	(337,889)	f	Fish	f	f	f	4320	Hollowgarde	0	0	f		0	f	f	1
171	5	{169,170,474}		0	1296	f	(1449,686)	f	Gold	f	f	f	687	Mossmore	0	0	f		0	f	f	2
267	0	{144,253,256,268,289}		0	382	f	(1087,936)	f	Glass	f	f	f	3015	Tabanteki	0	0	f		0	f	f	4
304	0	{302,303,306,306,314}		0	311	f	(1645,520)	f	Grain	f	f	f	3634	Wolrion	0	0	f		0	f	f	3
276	7	{241,242,251,275,277,281}		0	150	f	(1116,670)	f	Paper	f	f	f	155	Kimnia	0	0	f		0	f	f	1
10	0	{3,5,9,11,12,28}		0	395	f	(790,1273)	t	Grain	f	f	f	4388	Arakuru	0	0	f		0	f	f	3
284	7	{274,282,283,286,287}		0	165	f	(949,733)	t	Glass	f	f	f	248	Gobafidi	0	0	f		0	f	f	1
104	2	{99,100,102,103,110}		0	342	t	(592,722)	f	Paper	f	f	f	4057	Narakare	0	0	f		0	f	f	2
359	2	{336,340,352,353,356,357}		0	388	f	(1908,567)	f	Fur	f	f	f	3662	Qamatlong	0	0	f		0	f	f	1
198	9	{193,196,197,199,201}		0	112	f	(1188,279)	f	Fur	f	f	f	287	Mesane	0	0	f		0	f	f	1
280	7	{277,279,281,282,433}		0	165	f	(1015,637)	t	Glass	f	f	f	242	Mandujang	0	0	f		0	f	f	1
737	2	{733,734,736,738,739}		0	337	f	(3103,331)	t	Fruits	f	f	f	3996	Mankalane	0	0	f		0	f	f	1
776	2	{775,777,779}		0	353	t	(3035,132)	f	Chocolate	f	f	f	2711	Mobane	0	0	f		0	f	f	2
263	5	{294,415}		0	1260	f	(1395,909)	f	Iron	f	f	f	815	Seria	0	0	f		0	f	f	4
89	5	{88,90}		0	1250	t	(369,817)	f	Precious Stones	f	f	f	763	Omanie	0	0	f		0	f	f	4
184	9	{183,185,222}		0	125	t	(1379,389)	f	Fur	f	f	f	230	Genthanie	0	0	f		0	f	f	3
936	0	{927,934,935,937}		0	276	t	(2585,1332)	t	Cotton	f	f	f	3001	Babong	0	0	f		0	f	f	1
146	0	{145,147,297}		0	342	t	(1204,1008)	t	Ivory	f	f	f	4805	Quseng	0	0	f		0	f	f	3
498	1	{496,505,506}		0	172	t	(1188,1260)	f	Glass	f	f	f	797	Meweng	0	0	f		0	f	f	3
355	2	{354,356}		0	324	t	(2014,576)	f	Ivory	f	f	f	3603	Lethagonami	0	0	f		0	f	f	1
1016	0	{1013,1015,1017,1032}		0	345	f	(4019,1393)	f	Paper	f	f	f	4943	Danzibanyatsi	0	0	f		0	f	f	3
36	0	{34,35,37,36}		0	332	t	(1003,1172)	f	Grain	f	f	f	4954	Kulembu	0	0	f		0	f	f	3
360	0	{361,362,387,443}		0	379	t	(1440,1269)	f	Rare Wood	f	f	f	3722	Salkal	0	0	f		0	f	f	1
1	0	{2,3}		0	390	t	(781,1377)	f	Livestock	f	f	f	3647	Saldakuwa	0	0	f		0	f	f	1
548	0	{540,547,549,550}		0	328	t	(1354,2304)	f	Glass	f	f	f	3446	Kawa	0	0	f		0	f	f	3
266	2	{259,260,262,289,369,484}		0	385	f	(1379,958)	f	Salt	f	f	f	4012	Lahandja	0	0	f		0	f	f	3
309	2	{306,308,310,311,421,422}		0	363	f	(1663,639)	f	Rare Wood	f	f	f	3389	Namaferu	0	0	f		0	f	f	1
326	9	{324,325,327}		0	127	t	(1802,340)	f	Fish	f	f	f	167	Moine	0	0	f		0	f	f	1
27	0	{25,26,29,30,48,49,53}		0	312	f	(803,1134)	t	Wool	f	f	f	3420	Hukuhaba	0	0	f		0	f	f	2
214	2	{212,216}		0	309	t	(1062,463)	f	Wine	f	f	f	3225	Malume	0	0	f		0	f	f	3
335	2	{333,358,432}		0	324	t	(1840,540)	f	Paper	f	f	f	4357	Vulembu	0	0	f		0	f	f	2
412	5	{395,410,411}		0	1243	f	(1636,790)	f	Raw Stone	f	f	f	702	Allanrys	0	0	f		0	f	f	3
215	0	{0}		0	266	t	(909,475)	f	Fur	f	f	f	3778	Kilanga	0	0	f		0	f	f	2
632	2	{629,630,631,633}		0	317	t	(2441,317)	f	Fish	f	f	f	4480	Oshirara	0	0	f		0	f	f	1
489	5	{470,488,490,491}		0	1252	f	(1258,1357)	f	Coal	f	f	f	756	Lofale	0	0	f		0	f	f	2
250	2	{242,243,247,249,251,253}		0	343	f	(1177,803)	t	Glass	f	f	f	3190	Pokojea	0	0	f		0	f	f	1
374	1	{373,375,458,461}		0	132	f	(1714,864)	f	Glass	f	f	f	606	Selerobe	0	0	f		0	f	f	3
398	5	{397,399,400,461,462}		0	1072	f	(1721,772)	f	Spices	f	f	f	626	Tlothe	0	0	f		0	f	f	1
399	5	{397,398,400,405,407}		0	1197	f	(1719,763)	f	Coal	f	f	f	686	Iwagata	0	0	f		0	f	f	4
392	5	{372,391,393,394}		0	1104	f	(1573,830)	f	Coal	f	f	f	834	Mutsutsukawa	0	0	f		0	f	f	1
393	5	{391,392,394,414,419}		0	1062	f	(1595,803)	f	Tin	f	f	f	616	Changchong	0	0	f		0	f	f	1
243	0	{240,242,244,247,250}		0	272	f	(1186,742)	f	Grain	f	f	f	4391	Meishui	0	0	f		0	f	f	1
381	1	{379,380,382,385,445,446}		0	144	f	(1573,1168)	f	Spices	f	f	f	715	Khairmani	0	0	f		0	f	f	1
108	2	{106,107,109,113}		0	339	t	(738,767)	f	Grain	f	f	f	3554	Nogoonkh	0	0	f		0	f	f	2
829	5	{823,828,830,831,832}		0	1104	f	(3431,135)	f	Spices	f	f	f	829	Hamsu	0	0	f		0	f	f	3
269	0	{141,268,270,272,273}		0	258	f	(1010,918)	f	Livestock	f	f	f	4156	Taewang	0	0	f		0	f	f	1
879	2	{872,878,884,885}		0	332	t	(4066,286)	f	Livestock	f	f	f	4437	Hamchaek	0	0	f		0	f	f	1
380	1	{379,381,446,447,448}		0	164	f	(1645,1078)	t	Ivory	f	f	f	776	Sinuihung	0	0	f		0	f	f	2
366	0	{363,365,367,368,383,384}		0	305	f	(1406,1111)	f	Sugar	f	f	f	3144	Sinuicheon	0	0	f		0	f	f	3
368	0	{299,366,367,369,383,484}		0	258	t	(1384,1055)	f	Sugar	f	f	f	4348	Taigaa	0	0	f		0	f	f	2
375	1	{373,374,376,454,456}		0	103	f	(1683,904)	f	Ivory	f	f	f	545	Sogusi	0	0	f		0	f	f	2
383	1	{366,368,369,371,378,382,384}		0	167	f	(1435,1021)	f	Precious Stones	f	f	f	523	Nurhakisla	0	0	f		0	f	f	2
415	2	{263,264,265,292,293,294,416,417,483}		0	384	f	(1384,817)	f	Fruits	f	f	f	3949	Jirozmian	0	0	f		0	f	f	1
447	0	{380,446,448}		0	355	t	(1676,1199)	f	Glass	f	f	f	4718	Yasousar	0	0	f		0	f	f	1
440	1	{438,439,465,466}		0	143	t	(2077,1503)	f	Paper	f	f	f	733	As	0	0	f		0	f	f	2
485	2	{265,298,388,389,390,415,416,462}		0	310	f	(1453,846)	f	Salt	f	f	f	3946	Sasiyyah	0	0	f		0	f	f	1
490	5	{470,472,489,491}		0	1009	f	(1240,1368)	t	Raw Stone	f	f	f	705	Etadfa	0	0	f		0	f	f	2
459	2	{455,457,458,460}		0	357	t	(1795,866)	f	Copper	f	f	f	2945	Mirut	0	0	f		0	f	f	1
409	5	{407,408,410,411}		0	1192	f	(1676,772)	f	Raw Stone	f	f	f	858	Wadifer	0	0	f		0	f	f	1
469	0	{468,470,473,488}		0	253	t	(1287,1359)	f	Rare Wood	f	f	f	4401	Sakarout	0	0	f		0	f	f	3
458	2	{374,456,457,459,460,461}		0	328	f	(1759,866)	f	Glass	f	f	f	2595	Mneesayr	0	0	f		0	f	f	2
493	0	{472,492,494}		0	380	t	(1177,1377)	f	Cotton	f	f	f	4480	Masyamas	0	0	f		0	f	f	3
479	2	{308,420,421,478,480}		0	343	f	(1606,684)	f	Tea and Coffee	f	f	f	3073	Rafhamloj	0	0	f		0	f	f	2
462	2	{398,400,401,402,461}		0	354	t	(1759,763)	f	Wood	f	f	f	3271	Wadireg	0	0	f		0	f	f	3
499	5	{496,505}		0	1245	f	(1204,1323)	f	Coal	f	f	f	764	Choinuur	0	0	f		0	f	f	2
443	0	{360,361,444}		0	258	t	(1476,1354)	f	Tea and Coffee	f	f	f	4375	Panchun	0	0	f		0	f	f	3
413	5	{414,419,420}		0	1062	f	(1613,776)	t	Silver	f	f	f	769	Yatori	0	0	f		0	f	f	2
477	2	{166,419,420,478,479,516}		0	354	f	(1559,700)	f	Fruits	f	f	f	4395	Kumaraha	0	0	f		0	f	f	2
501	5	{488,502}		0	1128	f	(1249,1332)	f	Salt	f	f	f	766	Yahakonai	0	0	f		0	f	f	1
444	0	{361,387,443,445}		0	380	t	(1521,1298)	f	Fur	f	f	f	4873	Qahanieh	0	0	f		0	f	f	3
445	0	{381,385,386,44,446}		0	378	t	(1539,1231)	f	Rare Wood	f	f	f	3892	Arisyoun	0	0	f		0	f	f	1
442	1	{441}		0	139	t	(1829,1548)	f	Glass	f	f	f	636	Tel	0	0	f		0	f	f	1
453	2	{376,377,454}		0	303	t	(1721,990)	f	Livestock	f	f	f	2656	Khanayah	0	0	f		0	f	f	3
404	5	{425}		0	1102	f	(1766,738)	f	Coal	f	f	f	895	As	0	0	f		0	f	f	2
468	0	{467,469,470,471}		0	259	t	(1278,1397)	f	Fruits	f	f	f	3295	Saysan	0	0	f		0	f	f	4
418	2	{390,391,416,419,434,483}		0	378	f	(1512,801)	f	Salt	f	f	f	2591	Khorranab	0	0	f		0	f	f	3
448	0	{380,447,449,450}		0	392	t	(1683,1168)	t	Fur	f	f	f	4558	Alaroft	0	0	f		0	f	f	2
500	5	{502,504,506}		0	1210	f	(1231,1312)	f	Tin	f	f	f	889	Iliborlu	0	0	f		0	f	f	1
488	1	{469,470,473,487,489,501,502,503}		0	125	f	(1273,1316)	f	Ivory	f	f	f	588	Adankum	0	0	f		0	f	f	1
471	0	{467,468,470,472}		0	371	t	(1233,1415)	f	Paper	f	f	f	3839	Seafurah	0	0	f		0	f	f	1
232	2	{226,227,233,238,241,277,278}		0	303	f	(1159,549)	f	Chocolate	f	f	f	4338	Kivuadi	0	0	f		0	f	f	1
491	5	{489,490,492}		0	1042	f	(1222,1348)	t	Coal	f	f	f	674	Rausoka	0	0	f		0	f	f	4
495	1	{494,497}		0	116	t	(1114,1354)	f	Glass	f	f	f	641	Barekawa	0	0	f		0	f	f	1
450	0	{448,449,451,452}		0	250	f	(1717,1138)	f	Grain	f	f	f	3152	Tanimotu	0	0	f		0	f	f	1
452	0	{450,451}		0	271	t	(1699,1035)	f	Glass	f	f	f	3201	Rakawald	0	0	f		0	f	f	1
407	5	{399,405,406,408,409,421}		0	1219	f	(1681,749)	t	Precious Stones	f	f	f	660	Niupia	0	0	f		0	f	f	2
408	5	{407,409,410,420,421}		0	1044	f	(1651,758)	f	Spices	f	f	f	614	Utusi	0	0	f		0	f	f	1
438	1	{439,440}		0	125	t	(1993,1449)	f	Paper	f	f	f	598	Fetofesia	0	0	f		0	f	f	1
420	2	{408,410,413,419,421,477,478,479}		0	354	f	(1604,713)	f	Copper	f	f	f	3654	Fohi	0	0	f		0	f	f	2
72	0	{70,71,73,74,75,94,95}		0	357	f	(589,895)	f	Cotton	f	f	f	4445	Geelide	0	0	f		0	f	f	3
106	2	{103,105,107,108,109}		0	326	f	(684,760)	t	Fruits	f	f	f	3297	Seafave	0	0	f		0	f	f	3
225	2	{218,219,221,224,226,227}		0	345	f	(1199,466)	t	Fruits	f	f	f	2749	Vumbavua	0	0	f		0	f	f	1
778	2	{774,777,779,781}		0	384	t	(2978,94)	f	Fruits	f	f	f	4192	Sobalevu	0	0	f		0	f	f	3
176	2	{160,162,177}		0	332	t	(1462,463)	f	Salt	f	f	f	4360	Tekatiratai	0	0	f		0	f	f	3
99	0	{81,97,98,100,102,104}		0	307	f	(567,785)	t	Grain	f	f	f	3846	Nuotebiki	0	0	f		0	f	f	1
47	0	{44,45,46,48,49,50,138}		0	311	f	(907,1087)	t	Cotton	f	f	f	4164	Hokitakere	0	0	f		0	f	f	3
789	2	{787,788}		0	332	t	(3241,64)	f	Tea and Coffee	f	f	f	4159	Mapuapara	0	0	f		0	f	f	1
349	5	{346,350}		0	1110	f	(1912,511)	f	Salt	f	f	f	816	Faleamalo	0	0	f		0	f	f	1
1093	0	{965,969,1092}		0	326	f	(3312,1533)	f	Fruits	f	f	f	3294	A'ufaga	0	0	f		0	f	f	1
279	7	{277,280,433}		0	161	t	(1015,589)	t	Paper	f	f	f	173	Telefuiva	0	0	f		0	f	f	2
357	2	{356,358,359}		0	365	t	(1946,619)	f	Salt	f	f	f	4192	Lofakulei	0	0	f		0	f	f	1
235	2	{155,179,180,229,231,234}		0	313	f	(1285,576)	f	Salt	f	f	f	3857	Ivorgarde	0	0	f		0	f	f	4
430	0	{312,427,428,429,431,42}		0	256	f	(1741,594)	f	Rare Wood	f	f	f	4318	Glockrath	0	0	f		0	f	f	1
457	2	{455,456,458,459}		0	319	f	(1791,913)	f	Wood	f	f	f	4288	Charward	0	0	f		0	f	f	1
470	0	{468,469,471,472,488,489,490}		0	389	f	(1249,1379)	t	Sugar	f	f	f	3801	Ivoryham	0	0	f		0	f	f	3
481	2	{164,165,307,480,482,483}		0	361	f	(1568,625)	f	Sugar	f	f	f	4127	Dawnglen	0	0	f		0	f	f	2
148	2	{147,149,255,296}		0	312	f	(1235,954)	f	Wine	f	f	f	2837	Dreadwall	0	0	f		0	f	f	1
547	1	{540,541,545,546,548}		0	107	t	(1408,2344)	f	Ivory	f	f	f	631	Aerahaben	0	0	f		0	f	f	1
621	1	{0}		0	117	t	(499,2659)	f	Paper	f	f	f	586	Legstead	0	0	f		0	f	f	3
900	0	{895,896,899,901}		0	263	f	(3991,650)	t	Tobacco	f	f	f	4297	Flammore	0	0	f		0	f	f	3
824	5	{819,820,821,823,825}		0	1149	f	(3402,135)	f	Raw Stone	f	f	f	866	Sleetdrift	0	0	f		0	f	f	4
109	2	{103,106,108,110,111,112,113,114}		0	382	f	(661,729)	f	Rare Wood	f	f	f	4392	Ycemire	0	0	f		0	f	f	2
228	2	{223,224,227,229,231,233}		0	318	f	(1249,499)	t	Wood	f	f	f	2654	Fljot	0	0	f		0	f	f	2
264	5	{265,289,415}		0	1240	f	(1420,918)	f	Copper	f	f	f	727	Meoalfell	0	0	f		0	f	f	3
339	5	{336,337,338,340,350}		0	1162	f	(1885,542)	f	Iron	f	f	f	671	Hraunaheior	0	0	f		0	f	f	1
258	5	{257,259,260,261,294}		0	1245	f	(1341,929)	f	Raw Stone	f	f	f	759	Hagbarosholmr	0	0	f		0	f	f	1
618	1	{616,619,620}		0	115	t	(666,2515)	f	Paper	f	f	f	510	Kollsvik	0	0	f		0	f	f	1
956	0	{948,949,955,957,958,962,963}		0	313	f	(3195,1341)	f	Precious Goods	f	f	f	3555	Hafsloekr	0	0	f		0	f	f	2
362	0	{360,363,365,386,387}		0	302	t	(1429,1224)	f	Grain	f	f	f	3448	Hrafnstoptir	0	0	f		0	f	f	4
968	0	{967,989,990,1003}		0	260	t	(3567,1323)	f	Spices	f	f	f	3267	Eskiholt	0	0	f		0	f	f	1
341	5	{342}		0	1207	f	(1854,513)	f	Tin	f	f	f	720	Jokulsarhlio	0	0	f		0	f	f	2
725	0	{724,724,726,727}		0	338	t	(3184,506)	t	Rare Wood	f	f	f	4883	Hafgrimsfjoror	0	0	f		0	f	f	4
287	2	{271,273,274,284,286}		0	367	f	(970,826)	f	Tobacco	f	f	f	3509	Riocarí	0	0	f		0	f	f	1
861	9	{859,860,862,863,864}		0	136	f	(3739,207)	f	Fur	f	f	f	196	Jagar	0	0	f		0	f	f	1
377	1	{376,378,453}		0	167	f	(1676,1001)	f	Precious Goods	f	f	f	721	Architanas	0	0	f		0	f	f	2
364	0	{363,384,385,386}		0	254	f	(1476,1170)	f	Sugar	f	f	f	4798	Nulriel	0	0	f		0	f	f	1
958	0	{945,956,957,958,961,962}		0	372	f	(3118,1366)	f	Ivory	f	f	f	4312	Sinra	0	0	f		0	f	f	4
914	0	{912,913,915}		0	354	t	(3787,688)	t	Paper	f	f	f	3296	Immia	0	0	f		0	f	f	3
989	0	{968,990,991}		0	321	t	(3632,1271)	f	Fish	f	f	f	3396	Makourama	0	0	f		0	f	f	1
131	2	{129,132}		0	372	f	(882,803)	f	Sugar	f	f	f	2806	Pago	0	0	f		0	f	f	2
71	0	{69,70,72,95,96}		0	377	f	(659,864)	t	Spices	f	f	f	3020	Abenastina	0	0	f		0	f	f	1
9	0	{5,6,8,10,28,29}		0	346	f	(839,1253)	f	Wool	f	f	f	3323	Tápiz	0	0	f		0	f	f	2
316	9	{317,318}		0	120	t	(1678,414)	f	Precious Goods	f	f	f	232	Ejimare	0	0	f		0	f	f	2
1118	5	{1080,1081,1116,1117,1119}		0	1217	f	(3191,2052)	f	Iron	f	f	f	872	Limonum	0	0	f		0	f	f	4
1175	0	{1172,1174,1176,1177,1178}		0	317	t	(2504,2392)	f	Wood	f	f	f	3155	Caudium	0	0	f		0	f	f	3
434	2	{289,416,417,418,419,474,516}		0	349	f	(1494,785)	t	Grain	f	f	f	4382	Armorica	0	0	f		0	f	f	2
1038	2	{1026,1037,1039,1041,1042}		0	354	f	(3816,1728)	f	Paper	f	f	f	3674	Dianinum	0	0	f		0	f	f	1
606	2	{604,605,607,615,616}		0	301	f	(832,2475)	f	Paper	f	f	f	3807	Emporiae	0	0	f		0	f	f	4
920	0	{919,920,921,922}		0	326	t	(3472,695)	f	Wood	f	f	f	3472	Bilbilis	0	0	f		0	f	f	1
510	0	{509}		0	251	t	(556,1442)	f	Grain	f	f	f	4250	Ostium	0	0	f		0	f	f	4
742	2	{740,741,743,745}		0	323	t	(3107,225)	f	Rare Wood	f	f	f	3019	Sinope	0	0	f		0	f	f	2
732	2	{730,731,733,738}		0	305	t	(3186,389)	t	Livestock	f	f	f	4071	Atrans	0	0	f		0	f	f	4
919	0	{920,921}		0	368	t	(3422,637)	f	Glass	f	f	f	4045	Concangis	0	0	f		0	f	f	3
1083	5	{1078,1084,1085,1105}		0	1123	f	(3186,1906)	f	Coal	f	f	f	692	Tuder	0	0	f		0	f	f	3
870	9	{868,869,871,872,880}		0	151	f	(3985,171)	f	Ivory	f	f	f	189	Selymbria	0	0	f		0	f	f	4
845	9	{844,846,851,852}		0	123	t	(3533,188)	f	Fur	f	f	f	151	Cannabiaca	0	0	f		0	f	f	1
881	9	{880,882,883}		0	192	t	(4133,119)	f	Glass	f	f	f	274	Catania	0	0	f		0	f	f	2
712	2	{702,710,711,713,714,1217}		0	302	f	(2657,796)	f	Livestock	f	f	f	3133	Portus	0	0	f		0	f	f	2
627	2	{626,628,629}		0	370	t	(2349,313)	f	Fruits	f	f	f	4208	Odessus	0	0	f		0	f	f	2
834	5	{827,828,833,835}		0	1060	f	(3454,175)	f	Iron	f	f	f	795	Tenedo	0	0	f		0	f	f	3
665	0	{664,666,678,679,680}		0	362	t	(2770,441)	f	Paper	f	f	f	3238	Mursa	0	0	f		0	f	f	2
520	2	{512,523}		0	333	t	(454,1962)	f	Tobacco	f	f	f	2676	Velipa	0	0	f		0	f	f	2
926	0	{923}		0	270	t	(3325,967)	f	Fish	f	f	f	3872	Seveyungri	0	0	f		0	f	f	4
1054	2	{1050,1053,1055}		0	337	t	(3699,1989)	f	Copper	f	f	f	3932	Yelalabuga	0	0	f		0	f	f	2
726	0	{725,727,731,731}		0	354	t	(3199,459)	t	Cotton	f	f	f	4481	Anarechny	0	0	f		0	f	f	1
546	1	{545,547}		0	140	t	(1440,2419)	f	Fish	f	f	f	708	Calacadis	0	0	f		0	f	f	4
589	2	{588,590,608,609}		0	308	f	(994,2536)	f	Paper	f	f	f	2743	Abylune	0	0	f		0	f	f	1
1052	2	{1050,1051,1053,1057,1059}		0	373	f	(3648,1958)	f	Grain	f	f	f	3729	Liquasa	0	0	f		0	f	f	1
1127	7	{1101,1109,1110,1113,1114,1126}		0	147	t	(2914,1863)	t	Coal	f	f	f	166	Puritin	0	0	f		0	f	f	1
1143	0	{1129,1131,1132,1142,1144}		0	314	t	(2790,1755)	f	Fish	f	f	f	3436	Posegia	0	0	f		0	f	f	2
1169	5	{1153,1154,1170}		0	1216	f	(2889,2246)	f	Copper	f	f	f	765	Belipis	0	0	f		0	f	f	1
224	2	{221,222,223,225,227,228}		0	337	f	(1244,457)	t	Salt	f	f	f	2908	Thelor	0	0	f		0	f	f	1
788	2	{787,789}		0	321	t	(3253,38)	f	Wine	f	f	f	4133	Tsunareth	0	0	f		0	f	f	1
526	2	{524,525}		0	377	t	(495,2176)	f	Grain	f	f	f	3163	Tynea	0	0	f		0	f	f	3
21	0	{17,18,20,22}		0	390	t	(650,1163)	t	Cotton	f	f	f	3809	Geythis	0	0	f		0	f	f	3
1060	2	{1058,1059,1061,1065}		0	332	t	(3504,1998)	f	Glass	f	f	f	3703	Tempemon	0	0	f		0	f	f	2
315	2	{302,314}		0	337	t	(1638,445)	f	Paper	f	f	f	4375	Thalareth	0	0	f		0	f	f	1
754	2	{747,753,755,758}		0	354	t	(3247,301)	f	Glass	f	f	f	3986	Tethton	0	0	f		0	f	f	1
705	0	{704,706}		0	370	t	(2860,990)	f	Fruits	f	f	f	3918	Nepturia	0	0	f		0	f	f	2
118	7	{116,117,121}		0	178	t	(639,553)	t	Fish	f	f	f	172	Paciris	0	0	f		0	f	f	1
867	9	{866,868,871}		0	175	t	(3883,110)	f	Fur	f	f	f	292	Levialean	0	0	f		0	f	f	2
843	5	{837,842,844,846}		0	1073	f	(3499,164)	f	Gold	f	f	f	678	Boyrem	0	0	f		0	f	f	2
555	7	{553,554,556,557,596}		0	161	f	(1186,2387)	f	Paper	f	f	f	237	Aciolis	0	0	f		0	f	f	3
885	2	{879,884,886,887}		0	327	t	(4120,387)	f	Grain	f	f	f	3113	Hydgia	0	0	f		0	f	f	2
1056	2	{1053,1055,1057}		0	375	t	(3613,2167)	f	Copper	f	f	f	3281	Sireria	0	0	f		0	f	f	3
897	0	{887,888,896,898,899}		0	351	t	(4072,580)	f	Sugar	f	f	f	3815	Liquiri	0	0	f		0	f	f	3
1030	0	{1017,1018,1029,1031,1032}		0	370	f	(4053,1521)	f	Wool	f	f	f	4500	Navathis	0	0	f		0	f	f	2
673	0	{669,672,674,675,676,722}		0	362	f	(2991,598)	f	Fur	f	f	f	3843	Liquasa	0	0	f		0	f	f	2
841	5	{839,840,847,848}		0	1188	t	(3486,96)	f	Raw Stone	f	f	f	650	Salania	0	0	f		0	f	f	2
537	0	{536,538,549,552}		0	284	t	(1219,2198)	f	Sugar	f	f	f	4328	Aciopis	0	0	f		0	f	f	2
1017	0	{1015,1016,1018,1030,1032}		0	350	t	(4077,1447)	f	Fish	f	f	f	3738	Berylora	0	0	f		0	f	f	4
1079	7	{1068,1070,1078,1080,1082}		0	175	f	(3297,1976)	f	Rare Wood	f	f	f	187	Riverem	0	0	f		0	f	f	2
167	0	{164,165,166,168,173,476}		0	293	f	(1505,641)	t	Glass	f	f	f	3140	Merlean	0	0	f		0	f	f	1
122	7	{119,121,123}		0	154	t	(733,495)	f	Fish	f	f	f	237	Amphireth	0	0	f		0	f	f	1
863	2	{861,862,864,875}		0	306	t	(3694,283)	f	Tobacco	f	f	f	4113	Abyrey	0	0	f		0	f	f	1
1018	0	{1017,1019,1029,1030}		0	304	t	(4136,1546)	f	Livestock	f	f	f	4762	Scylor	0	0	f		0	f	f	1
550	0	{548,549,551,554}		0	266	t	(1298,2394)	f	Wool	f	f	f	3654	Belilean	0	0	f		0	f	f	2
559	7	{556,558,560}		0	173	t	(1147,2542)	f	Silk	f	f	f	183	Donoch	0	0	f		0	f	f	1
525	2	{522,524,526}		0	354	t	(405,2169)	f	Precious Goods	f	f	f	2643	Levialore	0	0	f		0	f	f	1
1048	2	{1042,1043,1047}		0	333	f	(3670,1755)	t	Wood	f	f	f	3732	Aquasa	0	0	f		0	f	f	1
538	0	{537,539,540,549}		0	297	t	(1298,2180)	f	Wool	f	f	f	3333	Ashamon	0	0	f		0	f	f	1
126	7	{113,124,125,127,128,285,433}		0	158	f	(886,668)	t	Precious Goods	f	f	f	165	Salaren	0	0	f		0	f	f	1
1045	2	{1008,1009,1044,1046}		0	386	f	(3517,1611)	t	Copper	f	f	f	2584	Tsuloch	0	0	f		0	f	f	1
567	5	{566,568,569}		0	1097	t	(1170,2767)	f	Salt	f	f	f	892	Hytin	0	0	f		0	f	f	2
188	9	{187}		0	193	t	(1348,283)	f	Spices	f	f	f	195	Chaszuth	0	0	f		0	f	f	1
921	0	{919,920,922}		0	346	t	(3508,679)	f	Wool	f	f	f	3922	Microd	0	0	f		0	f	f	2
695	5	{687,694,696}		0	1217	f	(2830,706)	f	Copper	f	f	f	848	Kaliz	0	0	f		0	f	f	3
301	0	{300,302,303,482,483}		0	313	f	(1604,513)	f	Fur	f	f	f	4938	Taltahrar	0	0	f		0	f	f	4
588	2	{573,586,587,590,589,609,611}		0	331	f	(958,2578)	f	Fruits	f	f	f	3621	Vazulzak	0	0	f		0	f	f	2
523	2	{520,521,524}		0	387	t	(499,1980)	f	Salt	f	f	f	3972	Tunkhudduk	0	0	f		0	f	f	1
630	2	{628,629,631,632}		0	303	t	(2367,387)	f	Livestock	f	f	f	3059	Miggiddoz	0	0	f		0	f	f	3
699	5	{698,700,1216}		0	1022	f	(2779,738)	f	Tin	f	f	f	885	Kaakrahnath	0	0	f		0	f	f	2
522	2	{518,519,521,524,525}		0	354	t	(333,2083)	f	Fish	f	f	f	3126	Joggrox	0	0	f		0	f	f	2
686	5	{678,684,687,685,696}		0	1151	f	(2768,629)	f	Salt	f	f	f	609	Nakkuss	0	0	f		0	f	f	1
652	2	{650,651,653,655}		0	343	t	(2662,90)	f	Fur	f	f	f	3644	Zukkross	0	0	f		0	f	f	2
1078	7	{1070,1077,1079,1082,1083,1084}		0	177	f	(3240,1938)	f	Coal	f	f	f	238	Rutago	0	0	f		0	f	f	1
614	1	{610,613,615,619}		0	173	f	(772,2569)	f	Ivory	f	f	f	703	Gato	0	0	f		0	f	f	3
1211	0	{0}		0	370	t	(3240,2324)	f	Fruits	f	f	f	4693	Ellaba	0	0	f		0	f	f	2
660	0	{659,661,662}		0	264	t	(2869,306)	f	Fur	f	f	f	3936	Maganango	0	0	f		0	f	f	3
554	0	{550,551,553,555,556}		0	357	t	(1228,2396)	f	Glass	f	f	f	4725	Ruhenhengeri	0	0	f		0	f	f	1
723	0	{672,721,722,724,725}		0	399	t	(3134,558)	f	Tea and Coffee	f	f	f	4000	Buye	0	0	f		0	f	f	3
1200	2	{1195,1197,1199,1200,1201}		0	385	t	(2502,2907)	f	Iron	f	f	f	3722	Ufecad	0	0	f		0	f	f	3
513	2	{512,514,515}		0	303	t	(526,1028)	f	Salt	f	f	f	3369	Mlankindu	0	0	f		0	f	f	1
28	0	{9,10,12,19,29}		0	281	f	(781,1226)	t	Fruits	f	f	f	4890	Mamo	0	0	f		0	f	f	2
802	2	{801,803,810,811}		0	327	t	(3271,119)	f	Salt	f	f	f	3254	Biharari	0	0	f		0	f	f	4
268	0	{141,144,267,269,273,289}		0	370	f	(1042,925)	f	Wool	f	f	f	3735	Kampagazi	0	0	f		0	f	f	2
1210	2	{1209}		0	304	t	(3355,2648)	f	Copper	f	f	f	3055	Apayo	0	0	f		0	f	f	1
1059	2	{1051,1052,1057,1058,1060,1061}		0	394	f	(3589,1931)	f	Livestock	f	f	f	4315	Kamudo	0	0	f		0	f	f	2
578	7	{577,579}		0	115	t	(1012,2896)	f	Glass	f	f	f	289	Atrophy	0	0	f		0	f	f	2
132	2	{131,133,286,288}		0	317	f	(900,812)	t	Paper	f	f	f	4173	Scythe	0	0	f		0	f	f	2
1163	5	{1162,1164}		0	1171	f	(2988,2306)	f	Raw Stone	f	f	f	694	Carthage	0	0	f		0	f	f	1
610	1	{609,611,612,613,614}		0	130	f	(832,2603)	f	Glass	f	f	f	663	Dawnbury	0	0	f		0	f	f	3
531	0	{530,532,533}		0	279	t	(832,2225)	f	Paper	f	f	f	4020	Quellton	0	0	f		0	f	f	1
648	2	{644,645,647}		0	366	t	(2702,283)	f	Salt	f	f	f	4041	Isolone	0	0	f		0	f	f	1
1161	0	{1159,1160,1162,1182}		0	334	f	(3009,2410)	f	Livestock	f	f	f	3167	Termina	0	0	f		0	f	f	1
713	2	{711,712,714}		0	347	t	(2614,799)	f	Sugar	f	f	f	3263	Krslav	0	0	f		0	f	f	1
1101	7	{1095,1096,1100,1102,1108,1109,1127,1128}		0	146	f	(2941,1706)	f	Rare Wood	f	f	f	156	Vsekolov	0	0	f		0	f	f	3
22	0	{21,23,24}		0	265	t	(686,1150)	f	Glass	f	f	f	4605	Democaea	0	0	f		0	f	f	1
536	0	{535,537,552,596}		0	341	t	(1098,2149)	f	Glass	f	f	f	4152	Myrini	0	0	f		0	f	f	2
33	0	{8,31,32,34,35}		0	258	f	(956,1217)	f	Fur	f	f	f	4136	Tylamnus	0	0	f		0	f	f	2
486	9	{65}		0	136	t	(1498,61)	f	Glass	f	f	f	208	Lamesus	0	0	f		0	f	f	2
670	0	{668,669,671,728}		0	351	f	(3019,477)	f	Livestock	f	f	f	3177	Alyros	0	0	f		0	f	f	2
1108	5	{1101,1102,1107,1109}		0	1274	f	(3013,1843)	f	Salt	f	f	f	856	Demike	0	0	f		0	f	f	1
1144	0	{1142,1143,1145,1147}		0	347	t	(2694,1791)	t	Wood	f	f	f	3251	Thyrespiae	0	0	f		0	f	f	2
1151	0	{1138,1139,1148,1150,1152}		0	382	t	(2484,1654)	f	Grain	f	f	f	4344	Eretrissos	0	0	f		0	f	f	3
735	2	{734,736,741}		0	341	t	(3033,288)	f	Tea and Coffee	f	f	f	3783	Heraclymna	0	0	f		0	f	f	4
1156	5	{1154,1155,1157}		0	1171	t	(3015,2262)	f	Raw Stone	f	f	f	812	Thuriliki	0	0	f		0	f	f	1
995	0	{992,994,996}		0	264	t	(3857,1208)	f	Fish	f	f	f	3639	Lampsomenus	0	0	f		0	f	f	1
629	2	{627,628,630,632}		0	389	t	(2389,355)	f	Fur	f	f	f	2695	Mareos	0	0	f		0	f	f	1
828	5	{826,827,829,832,833,834}		0	1198	f	(3436,153)	f	Silver	f	f	f	735	Phliesos	0	0	f		0	f	f	3
1069	5	{1067,1068}		0	1236	f	(3373,1980)	f	Copper	f	f	f	863	Oncheron	0	0	f		0	f	f	1
622	1	{0}		0	148	t	(454,2896)	f	Spices	f	f	f	507	Cumespiae	0	0	f		0	f	f	1
518	2	{519,521,522}		0	322	t	(328,1966)	f	Copper	f	f	f	2692	Myndasae	0	0	f		0	f	f	1
65	9	{483}		0	183	t	(1521,40)	f	Glass	f	f	f	265	Acomenion	0	0	f		0	f	f	1
584	5	{581,582,583,612}		0	1204	f	(855,2729)	f	Raw Stone	f	f	f	853	Psychrinitida	0	0	f		0	f	f	1
1170	5	{1153,1168,1169}		0	1054	t	(2857,2226)	f	Coal	f	f	f	787	Cumakros	0	0	f		0	f	f	1
207	2	{208,212}		0	360	t	(1028,349)	f	Copper	f	f	f	2915	Aigous	0	0	f		0	f	f	1
1130	0	{1098,1099,1100,1128,1129,1131}		0	395	f	(2862,1668)	f	Wool	f	f	f	3817	Gelaclea	0	0	f		0	f	f	1
1081	5	{1080,1082,1111,1112,1117,1118}		0	1056	f	(3184,2010)	f	Iron	f	f	f	858	Gythagoria	0	0	f		0	f	f	1
905	0	{877,892,904,906}		0	261	f	(3854,459)	f	Glass	f	f	f	4509	Elaticus	0	0	f		0	f	f	1
631	2	{630,632,633}		0	304	t	(2405,391)	f	Wood	f	f	f	2515	Morgocaea	0	0	f		0	f	f	3
826	5	{817,827,828}		0	1161	f	(3420,169)	f	Coal	f	f	f	607	Leontinitida	0	0	f		0	f	f	2
527	0	{528,529,530}		0	369	t	(684,2277)	f	Livestock	f	f	f	3708	Orastro	0	0	f		0	f	f	4
539	0	{538,540,541}		0	263	t	(1381,2180)	f	Ivory	f	f	f	3199	Himos	0	0	f		0	f	f	2
113	7	{108,109,114,120,124,126,127}		0	112	t	(778,679)	f	Rare Wood	f	f	f	231	Losse	0	0	f		0	f	f	1
1026	2	{1021,1025,1027,1037,1038,1039}		0	305	f	(3909,1733)	t	Iron	f	f	f	3213	Gorgox	0	0	f		0	f	f	1
1020	2	{1019,1021,1026,1027}		0	349	t	(4064,1715)	f	Ivory	f	f	f	3927	Paphateia	0	0	f		0	f	f	2
718	0	{682,717}		0	332	t	(2515,659)	f	Wood	f	f	f	3619	Hierinope	0	0	f		0	f	f	1
435	1	{436,437}		0	162	t	(1867,1440)	f	Paper	f	f	f	761	Lefkanthus	0	0	f		0	f	f	3
1158	5	{1159,1162}		0	1104	t	(3056,2317)	f	Iron	f	f	f	662	Olamum	0	0	f		0	f	f	3
604	0	{601,602,603,605,606,616,617}		0	347	f	(801,2376)	t	Livestock	f	f	f	3591	Rhypada	0	0	f		0	f	f	1
837	5	{836,838,842,843}		0	1014	f	(3474,171)	f	Salt	f	f	f	670	Himarnacia	0	0	f		0	f	f	2
1015	0	{1013,1014,1016,1017}		0	302	t	(4054,1377)	f	Livestock	f	f	f	3456	Katyros	0	0	f		0	f	f	2
741	2	{735,736,739,740,742}		0	321	t	(3046,245)	f	Fruits	f	f	f	4247	Thasseron	0	0	f		0	f	f	1
1134	0	{940,1098,1132,1133,1135}		0	300	f	(2781,1571)	t	Rare Wood	f	f	f	4374	Thassofa	0	0	f		0	f	f	2
556	7	{554,555,557,558,559}		0	126	t	(1161,2452)	f	Silk	f	f	f	215	Metens	0	0	f		0	f	f	3
1186	2	{1182,1185,1187,1188,1189,1190}		0	352	f	(2995,2610)	f	Grain	f	f	f	2800	Moleporobe	0	0	f		0	f	f	1
625	1	{624}		0	109	t	(2272,1503)	f	Spices	f	f	f	752	Nokapi	0	0	f		0	f	f	1
836	5	{835,837,44}		0	1129	t	(3478,187)	f	Salt	f	f	f	726	Qetika	0	0	f		0	f	f	1
1206	2	{1204,1205}		0	357	t	(3078,2937)	f	Wine	f	f	f	4108	Qetithing	0	0	f		0	f	f	1
1162	5	{1158,1159,1161,1163,1165,1166,1167,1182}		0	1046	f	(2973,2383)	f	Gold	f	f	f	814	Omudu	0	0	f		0	f	f	2
894	0	{889,890,893,895,903}		0	343	f	(3971,490)	t	Ivory	f	f	f	3689	Otjimna	0	0	f		0	f	f	1
690	2	{689,691,706,707}		0	345	t	(2956,778)	f	Paper	f	f	f	4166	Ekanbron	0	0	f		0	f	f	1
542	0	{541,543,545}		0	320	t	(1559,2315)	f	Grain	f	f	f	3838	Mitief	0	0	f		0	f	f	1
1089	7	{1074,1087,1088,1090,1094}		0	157	f	(3213,1643)	t	Paper	f	f	f	279	Kwano	0	0	f		0	f	f	1
1046	2	{1044,1045,1047,1049,1062}		0	395	f	(3494,1699)	f	Iron	f	f	f	2585	Movone	0	0	f		0	f	f	1
796	9	{795,797,798}		0	103	t	(3633,46)	f	Fur	f	f	f	198	Lobashe	0	0	f		0	f	f	2
585	5	{580,581,584,586,611,612}		0	1292	f	(916,2713)	f	Coal	f	f	f	854	Lotrowe	0	0	f		0	f	f	3
764	0	{0}		0	361	t	(3550,350)	f	Grain	f	f	f	4525	Thayatseng	0	0	f		0	f	f	1
664	0	{661,663,665,666,667}		0	257	t	(2815,391)	f	Fur	f	f	f	3018	Ongwema	0	0	f		0	f	f	2
1157	5	{1156}		0	1192	t	(3060,2300)	f	Copper	f	f	f	653	Okahadive	0	0	f		0	f	f	3
832	5	{828,829,831,833,840}		0	1226	f	(3454,130)	f	Tin	f	f	f	686	Kruba	0	0	f		0	f	f	1
763	0	{0}		0	357	t	(3583,321)	f	Wool	f	f	f	4106	Allankal	0	0	f		0	f	f	2
1201	2	{1197,1198,1200,1202}		0	314	t	(2649,2889)	f	Paper	f	f	f	3484	Nsabasena	0	0	f		0	f	f	1
1023	2	{1022,1024,1040}		0	305	t	(3877,1962)	t	Wine	f	f	f	2979	Dulevise	0	0	f		0	f	f	2
770	0	{0}		0	319	t	(3474,520)	f	Fish	f	f	f	3798	Kubuye	0	0	f		0	f	f	3
667	0	{663,664,666,668,667,676}		0	327	f	(2891,463)	f	Tobacco	f	f	f	3068	Saldanus	0	0	f		0	f	f	2
999	0	{998,1000,1011,1012,1013,1014}		0	395	f	(3798,1371)	f	Ivory	f	f	f	4783	Soha	0	0	f		0	f	f	3
708	0	{706,707}		0	352	t	(2965,1015)	f	Fish	f	f	f	3137	Rehovi	0	0	f		0	f	f	1
238	2	{232,233,237,239,240,241}		0	358	f	(1199,612)	f	Fur	f	f	f	2729	Oshidja	0	0	f		0	f	f	2
607	2	{601,605,606,608,609,615}		0	321	f	(889,2457)	f	Rare Wood	f	f	f	3498	Meyokabei	0	0	f		0	f	f	1
744	2	{0}		0	385	t	(3129,122)	f	Spices	f	f	f	4494	Pihane	0	0	f		0	f	f	2
521	2	{518,520,522,524}		0	314	t	(389,2041)	f	Salt	f	f	f	4354	Molepodibe	0	0	f		0	f	f	2
2	0	{1,3,4}		0	351	t	(862,1402)	f	Grain	f	f	f	4939	Thamalala	0	0	f		0	f	f	3
324	9	{320,323,326,327,328,329}		0	128	f	(1816,353)	f	Glass	f	f	f	217	Westwall	0	0	f		0	f	f	2
1111	5	{1081,1082,1112,1113}		0	1073	f	(3136,1935)	f	Precious Stones	f	f	f	807	Freyview	0	0	f		0	f	f	1
1107	5	{1102,1104,1106,1108,1109,1110}		0	1124	f	(3081,1841)	f	Salt	f	f	f	768	Bayhollow	0	0	f		0	f	f	1
569	5	{565,566,567,570,571}		0	1216	f	(1179,2745)	f	Coal	f	f	f	698	Frostvalley	0	0	f		0	f	f	1
534	0	{533,535,598}		0	343	t	(1001,2196)	f	Wool	f	f	f	3234	Smallstrand	0	0	f		0	f	f	1
767	0	{766}		0	339	t	(3403,405)	f	Spices	f	f	f	4898	Limestar	0	0	f		0	f	f	2
1188	2	{1186,1187,1189,1198,1202,1204}		0	307	f	(2862,2770)	f	Chocolate	f	f	f	3210	Southborough	0	0	f		0	f	f	2
512	2	{511,513}		0	311	t	(556,1069)	f	Glass	f	f	f	4008	Arrowstrand	0	0	f		0	f	f	1
1021	2	{1020,1022,1025,1026}		0	388	t	(3994,1823)	t	Grain	f	f	f	4336	Borville	0	0	f		0	f	f	1
353	2	{351,352,354,356,359}		0	313	t	(1951,520)	f	Iron	f	f	f	4425	Wintermoor	0	0	f		0	f	f	2
773	2	{774,775}		0	388	t	(2952,166)	f	Grain	f	f	f	3289	Marilet	0	0	f		0	f	f	2
1164	5	{1163,1165}		0	1104	f	(2934,2297)	f	Spices	f	f	f	667	Ironfield	0	0	f		0	f	f	4
1138	0	{1137,1139,1151}		0	269	t	(2536,1566)	f	Livestock	f	f	f	4310	Ruststar	0	0	f		0	f	f	2
1087	5	{1074,1086,1088,1089,1103}		0	1280	f	(3218,1778)	t	Raw Stone	f	f	f	680	Silenttown	0	0	f		0	f	f	4
947	0	{946,948,957}		0	260	t	(3125,1267)	f	Sugar	f	f	f	4778	Silvershore	0	0	f		0	f	f	1
721	0	{719,720,722,723}		0	258	t	(3157,612)	f	Tobacco	f	f	f	3368	Avinia	0	0	f		0	f	f	1
649	9	{650,651}		0	124	t	(2590,31)	f	Fur	f	f	f	181	Cálma	0	0	f		0	f	f	2
910	0	{908,911,912}		0	253	t	(3690,531)	f	Wood	f	f	f	3477	Virtos	0	0	f		0	f	f	3
121	7	{118,119,122}		0	139	t	(686,468)	t	Paper	f	f	f	282	Orodorm	0	0	f		0	f	f	1
437	1	{435,436,464}		0	171	t	(1960,1449)	f	Paper	f	f	f	523	Tomadura	0	0	f		0	f	f	1
1057	2	{1053,1056,1058,1059}		0	316	t	(3600,2066)	f	Wine	f	f	f	3908	Bulle	0	0	f		0	f	f	3
1173	0	{1172,1174}		0	277	t	(2522,2277)	f	Fruits	f	f	f	4624	Andanea	0	0	f		0	f	f	1
924	0	{925}		0	330	t	(3458,936)	f	Fish	f	f	f	3316	Grallón	0	0	f		0	f	f	1
1166	5	{1162,1165,1167}		0	1199	f	(2903,2410)	f	Salt	f	f	f	844	Gipuscay	0	0	f		0	f	f	1
321	9	{317,320,322,323,333}		0	142	f	(1750,425)	f	Precious Goods	f	f	f	255	Cagona	0	0	f		0	f	f	2
1123	7	{1115,1120,1122,1124,1126,1155}		0	131	t	(3042,2131)	t	Fish	f	f	f	186	Zamostile	0	0	f		0	f	f	4
305	0	{304,306,310,312,314}		0	352	f	(1665,538)	f	Fur	f	f	f	4498	Alzilavega	0	0	f		0	f	f	1
552	0	{536,537,549,551,553,596}		0	253	f	(1204,2223)	f	Glass	f	f	f	4933	Outiva	0	0	f		0	f	f	3
574	7	{573,575,587}		0	177	f	(1060,2716)	t	Precious Goods	f	f	f	214	Zaravila	0	0	f		0	f	f	2
970	2	{971,973,974}		0	350	t	(3966,2579)	f	Tobacco	f	f	f	4147	Sagoza	0	0	f		0	f	f	1
756	2	{755,757}		0	380	t	(3359,295)	f	Spices	f	f	f	4297	Bacourt	0	0	f		0	f	f	3
220	2	{193,194,195,199,219}		0	362	f	(1204,360)	f	Tin	f	f	f	3734	Cololimar	0	0	f		0	f	f	2
755	2	{754,756,757,758}		0	380	t	(3289,292)	f	Fur	f	f	f	4387	Grelly	0	0	f		0	f	f	4
1126	7	{1114,1115,1123,1124,1125,1127}		0	164	t	(2909,1996)	t	Glass	f	f	f	211	Sarsart	0	0	f		0	f	f	1
237	2	{233,234,236,238,239}		0	318	f	(1219,625)	f	Grain	f	f	f	2913	Vinmont	0	0	f		0	f	f	1
922	0	{920,921}		0	261	t	(3481,758)	f	Paper	f	f	f	4019	Beaufort	0	0	f		0	f	f	1
181	2	{180,182,183,223,230}		0	326	f	(1339,479)	t	Grain	f	f	f	2903	Puroux	0	0	f		0	f	f	3
88	5	{87,89,90}		0	1000	f	(369,826)	f	Raw Stone	f	f	f	653	Marlimar	0	0	f		0	f	f	4
249	2	{149,247,250,253,254,255}		0	388	f	(1181,900)	t	Fur	f	f	f	2940	Orsier	0	0	f		0	f	f	3
658	2	{565,657}		0	361	t	(2794,151)	f	Fur	f	f	f	3998	Whisperpeak	0	0	f		0	f	f	1
998	0	{996,997,999,1000,1014}		0	327	t	(3839,1337)	f	Cotton	f	f	f	4556	Lowbellow	0	0	f		0	f	f	1
717	0	{683,714,716,718}		0	354	t	(2563,661)	f	Livestock	f	f	f	4659	Thingorge	0	0	f		0	f	f	2
952	0	{950,951,953,967}		0	325	t	(3427,1264)	t	Wool	f	f	f	3690	Quickpeak	0	0	f		0	f	f	1
943	0	{932,942,944,1079}		0	358	f	(2961,1496)	t	Grain	f	f	f	4983	Talonhallow	0	0	f		0	f	f	3
750	2	{743,745,749,751,752}		0	357	t	(3186,148)	f	Iron	f	f	f	4342	Copperstead	0	0	f		0	f	f	3
1076	5	{1074,1075,1077,1084,1085,1086}		0	1182	f	(3274,1848)	f	Gold	f	f	f	788	Bonetrail	0	0	f		0	f	f	2
685	5	{684,686,696,697,698,715}		0	1207	f	(2752,661)	f	Copper	f	f	f	846	Barebank	0	0	f		0	f	f	4
619	1	{613,614,615,616,618,620}		0	109	f	(731,2560)	f	Paper	f	f	f	537	Onyxpeak	0	0	f		0	f	f	3
1071	5	{1063,1065,1066,1070,1072}		0	1280	f	(3416,1906)	f	Silver	f	f	f	807	Wrycanyon	0	0	f		0	f	f	1
892	0	{877,890,891,893,904,905}		0	345	f	(3890,434)	f	Tobacco	f	f	f	3269	Starkpeaks	0	0	f		0	f	f	2
1086	5	{1074,1076,1085,1087,1103}		0	1247	f	(3238,1811)	t	Raw Stone	f	f	f	700	Buelita	0	0	f		0	f	f	3
1179	0	{1171,1172,1178,1180,1190}		0	358	f	(2694,2415)	f	Glass	f	f	f	3775	Quecos	0	0	f		0	f	f	4
747	2	{738,746,748,753,754}		0	307	t	(3217,290)	f	Wood	f	f	f	4486	Pola	0	0	f		0	f	f	2
795	9	{796,798}		0	186	t	(3590,20)	f	Fur	f	f	f	154	Recalco	0	0	f		0	f	f	2
714	2	{712,713,715,716,717}		0	372	t	(2605,724)	f	Precious Goods	f	f	f	4467	Rejanes	0	0	f		0	f	f	2
790	5	{791,792}		0	1228	t	(3384,12)	f	Salt	f	f	f	628	Yusquile	0	0	f		0	f	f	3
1121	7	{1120,1122}		0	112	t	(3301,2160)	f	Coal	f	f	f	192	Carcos	0	0	f		0	f	f	2
1212	0	{0}		0	276	t	(3348,2326)	f	Cotton	f	f	f	4157	Jinoral	0	0	f		0	f	f	2
1090	0	{961,1089,1091,1092,1094}		0	380	f	(3209,1555)	t	Wool	f	f	f	3985	Guacan	0	0	f		0	f	f	1
1105	5	{1083,1085,1103,1104,1106}		0	1030	f	(3162,1841)	f	Raw Stone	f	f	f	622	Ditos	0	0	f		0	f	f	2
1122	7	{1120,1121,1123}		0	146	t	(3150,2203)	t	Ivory	f	f	f	251	Wiwiya	0	0	f		0	f	f	2
62	0	{61,63,66,67}		0	387	f	(778,947)	t	Tobacco	f	f	f	3596	Cuyatal	0	0	f		0	f	f	2
638	9	{636,637,639,640}		0	105	t	(2376,88)	f	Glass	f	f	f	222	Rerio	0	0	f		0	f	f	4
1094	0	{960,961,1088,1089,1090,1095}		0	397	f	(3110,1573)	f	Livestock	f	f	f	4203	Aposonate	0	0	f		0	f	f	2
955	0	{949,951,954,956,963,964}		0	337	f	(3280,1363)	f	Livestock	f	f	f	3601	Atijutla	0	0	f		0	f	f	1
884	2	{878,879,885,886,891}		0	347	f	(4027,349)	f	Fur	f	f	f	3150	Mipiles	0	0	f		0	f	f	3
270	0	{137,139,140,141,269,271,272}		0	264	f	(967,949)	f	Livestock	f	f	f	4650	Sarillos	0	0	f		0	f	f	2
818	5	{816,817,819}		0	1281	f	(3402,180)	f	Salt	f	f	f	874	Jalacho	0	0	f		0	f	f	1
768	0	{769}		0	261	t	(3535,449)	f	Glass	f	f	f	3415	Volnola	0	0	f		0	f	f	4
997	0	{991,992,996,998,1000}		0	255	f	(3744,1292)	f	Fruits	f	f	f	3500	Quilica	0	0	f		0	f	f	1
286	2	{128,132,271,284,287,288}		0	319	f	(934,790)	t	Tin	f	f	f	4114	Priguaque	0	0	f		0	f	f	1
76	2	{74,75,77,78,79}		0	393	t	(472,936)	f	Paper	f	f	f	2600	Trujirito	0	0	f		0	f	f	1
255	2	{147,148,149,249,254,256}		0	385	f	(1192,934)	t	Livestock	f	f	f	2676	Salamento	0	0	f		0	f	f	3
147	0	{145,146,148,255,256,296}		0	377	f	(1201,974)	t	Wool	f	f	f	3100	Aguanahu	0	0	f		0	f	f	1
327	9	{324,326,328}		0	181	t	(1813,333)	f	Fur	f	f	f	202	Cojulupe	0	0	f		0	f	f	3
345	5	{330,331,344,346,347}		0	1135	f	(1888,466)	f	Silver	f	f	f	739	Atinal	0	0	f		0	f	f	2
334	2	{323,329,333,335,343}		0	302	f	(1820,466)	f	Glass	f	f	f	3914	Jara	0	0	f		0	f	f	1
586	5	{575,580,581,585,587,588,611}		0	1256	f	(961,2676)	f	Coal	f	f	f	820	Trinilores	0	0	f		0	f	f	2
937	0	{934,936,938,1147}		0	370	t	(2617,1417)	f	Wood	f	f	f	3656	Ponlants	0	0	f		0	f	f	1
29	0	{9,26,27,28,30,32}		0	339	f	(819,1197)	t	Tea and Coffee	f	f	f	4334	Hepmagne	0	0	f		0	f	f	1
668	0	{663,667,669,670,728,729}		0	367	t	(2974,430)	f	Sugar	f	f	f	4953	Clerbiens	0	0	f		0	f	f	1
666	0	{664,665,667,676,677,678}		0	308	f	(2815,496)	f	Wood	f	f	f	3315	Oqaattaq	0	0	f		0	f	f	1
1112	5	{1081,1111,1113,1115,1116,1117}		0	1134	f	(3130,1998)	f	Tin	f	f	f	766	Napaluitsup	0	0	f		0	f	f	1
1182	0	{1160,1161,1162,1167,1181,1183,1185,1186}		0	320	f	(2991,2442)	f	Spices	f	f	f	4781	Cajemoros	0	0	f		0	f	f	1
848	9	{841,847,849}		0	124	t	(3496,88)	f	Fur	f	f	f	210	Penjachuca	0	0	f		0	f	f	2
1074	7	{1073,1075,1076,1086,1087,1089}		0	151	f	(3285,1786)	t	Coal	f	f	f	250	Chitecas	0	0	f		0	f	f	3
855	9	{854,856,857,858}		0	166	t	(3613,94)	f	Fish	f	f	f	198	Chesmore	0	0	f		0	f	f	2
1131	0	{1098,1129,1130,1132,1143}		0	294	f	(2833,1701)	t	Livestock	f	f	f	3803	Scarmouth	0	0	f		0	f	f	2
643	2	{642,644,645,646}		0	379	t	(2583,281)	f	Paper	f	f	f	2582	Canterster	0	0	f		0	f	f	1
978	2	{973,977,979,981,982}		0	322	f	(3922,2828)	f	Salt	f	f	f	3904	Autumncester	0	0	f		0	f	f	2
558	7	{556,557,559,560,590,591}		0	158	f	(1120,2513)	f	Silk	f	f	f	279	Greenwall	0	0	f		0	f	f	4
230	2	{180,181,223,229}		0	386	f	(1327,520)	t	Iron	f	f	f	4480	Brighstone	0	0	f		0	f	f	1
946	0	{945,947,957}		0	359	t	(3089,1269)	f	Grain	f	f	f	3335	Ocosingo	0	0	f		0	f	f	1
192	9	{189,191,193,196}		0	186	t	(1269,238)	f	Fur	f	f	f	176	Xalacoco	0	0	f		0	f	f	4
332	2	{313,322,333,431}		0	325	f	(1769,518)	f	Tobacco	f	f	f	2613	Jiutelende	0	0	f		0	f	f	1
292	0	{152,154,290,291,293,415,417,474}		0	337	f	(1336,747)	f	Glass	f	f	f	4346	Nutaarhivik	0	0	f		0	f	f	4
1085	5	{1076,1083,1084,1086,1003,1005}		0	1059	f	(3220,1843)	t	Salt	f	f	f	676	Kuumtu	0	0	f		0	f	f	2
193	9	{192,194,196,198,199,220}		0	113	f	(1204,268)	f	Ivory	f	f	f	222	Burdiac	0	0	f		0	f	f	2
814	2	{810,813,815,816}		0	370	f	(3350,144)	f	Salt	f	f	f	3721	Garmis	0	0	f		0	f	f	2
1145	0	{1144,1146,1147}		0	302	t	(2615,1823)	f	Fruits	f	f	f	3496	Lebridge	0	0	f		0	f	f	4
600	0	{532,533,593,599,601,602}		0	388	f	(954,2315)	t	Livestock	f	f	f	4124	Flushgard	0	0	f		0	f	f	1
1165	5	{1162,1164,1166,1167,1168}		0	1121	f	(2892,2338)	f	Silver	f	f	f	725	Thistlehelm	0	0	f		0	f	f	1
940	0	{939,941,942,1098,1134,1135,1136}		0	375	f	(2758,1528)	t	Spices	f	f	f	3949	Mekkadale	0	0	f		0	f	f	2
1103	5	{1085,1086,1087,1088,1102,1104,1105}		0	1109	f	(3177,1780)	f	Raw Stone	f	f	f	637	Sparkwall	0	0	f		0	f	f	2
158	0	{157,159,172,175,290}		0	312	f	(1415,632)	f	Fur	f	f	f	4143	Plumewatch	0	0	f		0	f	f	2
464	1	{436,437}		0	128	t	(1993,1449)	f	Precious Stones	f	f	f	534	Freelmorg	0	0	f		0	f	f	1
294	2	{151,257,258,261,293,295,415}		0	377	f	(1327,864)	f	Glass	f	f	f	2530	Mummadogh	0	0	f		0	f	f	1
290	0	{157,158,291,292,474}		0	273	f	(1411,688)	f	Fruits	f	f	f	4605	Finkipplurg	0	0	f		0	f	f	1
844	9	{836,837,843,845,846}		0	186	t	(3499,185)	f	Fur	f	f	f	210	Fili	0	0	f		0	f	f	2
1184	2	{1183,1185,1187}		0	304	t	(3168,2650)	f	Fruits	f	f	f	3398	Keenfa	0	0	f		0	f	f	1
573	7	{560,574,587,588,590}		0	140	f	(1071,2639)	t	Rare Wood	f	f	f	268	Dintindeck	0	0	f		0	f	f	1
794	5	{792,793}		0	1246	t	(3390,52)	f	Tin	f	f	f	818	Glostos	0	0	f		0	f	f	2
793	5	{791,792,794}		0	1192	t	(3419,37)	f	Copper	f	f	f	691	Imblin	0	0	f		0	f	f	1
115	7	{111,112,116,118,119}		0	159	f	(675,612)	f	Paper	f	f	f	279	Fonnipporp	0	0	f		0	f	f	3
959	0	{944,945,958,960,961}		0	318	f	(3065,1454)	f	Cotton	f	f	f	3461	Wigglegate	0	0	f		0	f	f	1
95	0	{71,72,94,96,97,98}		0	391	f	(634,857)	f	Tobacco	f	f	f	4637	Landbrunn	0	0	f		0	f	f	1
299	2	{297,298,368,484}		0	364	t	(1336,1044)	f	Iron	f	f	f	4255	Gerasweg	0	0	f		0	f	f	1
530	0	{527,529,531,532,602}		0	397	t	(799,2245)	t	Paper	f	f	f	4512	Knokberge	0	0	f		0	f	f	1
757	2	{755,756,758,806,807}		0	325	t	(3346,256)	f	Fur	f	f	f	3003	Périssons	0	0	f		0	f	f	1
779	2	{776,777,778,780,781,782}		0	397	t	(3025,90)	f	Wood	f	f	f	4206	Caluçon	0	0	f		0	f	f	1
587	5	{573,574,575,586,588}		0	1149	f	(995,2662)	f	Coal	f	f	f	730	Gailkirchen	0	0	f		0	f	f	2
43	0	{37,41,42,44,45}		0	371	f	(1039,1091)	f	Sugar	f	f	f	3875	Ansholz	0	0	f		0	f	f	3
1096	0	{960,1095,1097,1099,1100,1101}		0	359	f	(2982,1562)	f	Fur	f	f	f	3954	Macvan	0	0	f		0	f	f	1
880	9	{870,872,879,881,882}		0	125	t	(4063,216)	f	Fur	f	f	f	284	Mullindoran	0	0	f		0	f	f	1
957	0	{945,946,947,948,956,958}		0	386	f	(3130,1316)	f	Paper	f	f	f	3891	Dikkerk	0	0	f		0	f	f	2
738	2	{732,733,737,739,746,747}		0	311	t	(3172,328)	f	Tin	f	f	f	2784	Asdaal	0	0	f		0	f	f	2
980	1	{879,981}		0	155	t	(3796,2886)	f	Glass	f	f	f	525	Spreitenbach	0	0	f		0	f	f	2
601	2	{592,593,600,602,604,605,607,608}		0	336	f	(943,2376)	f	Salt	f	f	f	3072	Appenlach	0	0	f		0	f	f	1
1002	0	{990,1001,1003,1007,1008,1009,1010}		0	266	f	(3582,1409)	f	Cotton	f	f	f	4026	Poyslach	0	0	f		0	f	f	2
1041	2	{1038,1039,1040,1042,1047,150}		0	302	t	(3729,1836)	t	Glass	f	f	f	3712	Oudenhout	0	0	f		0	f	f	1
698	5	{697,699,715,1215,1216}		0	1030	f	(2758,727)	f	Copper	f	f	f	835	Valès	0	0	f		0	f	f	1
1058	2	{1057,1059,60}		0	302	t	(3546,2012)	f	Spices	f	f	f	3223	Brugleeuw	0	0	f		0	f	f	2
1213	0	{0}		0	358	t	(3436,2288)	f	Sugar	f	f	f	3154	Cassons	0	0	f		0	f	f	1
363	0	{362,364,365,366,384,386}		0	253	f	(1429,1183)	f	Sugar	f	f	f	4541	Tangerschau	0	0	f		0	f	f	3
152	0	{151,153,154,292,293}		0	313	f	(1296,805)	f	Paper	f	f	f	3622	Spalion	0	0	f		0	f	f	1
941	0	{933,939,940,942}		0	320	f	(2797,1507)	t	Grain	f	f	f	4262	Rethyndra	0	0	f		0	f	f	3
825	5	{819,823,824}		0	1058	f	(3420,139)	f	Iron	f	f	f	732	Kaisasina	0	0	f		0	f	f	1
575	7	{574,576,580,586,587}		0	170	f	(1006,2709)	t	Silk	f	f	f	152	Miadananitra	0	0	f		0	f	f	2
772	0	{0}		0	344	t	(3376,525)	f	Fruits	f	f	f	3198	Soavinatanana	0	0	f		0	f	f	2
702	2	{692,700,701,703,710,712}		0	307	f	(2756,783)	t	Wine	f	f	f	2788	Tsarasirabe	0	0	f		0	f	f	1
506	1	{498,503,504,505}		0	123	t	(1222,1258)	f	Ivory	f	f	f	713	Antsinimena	0	0	f		0	f	f	2
487	1	{473,488,503}		0	169	t	(1287,1278)	f	Dyes	f	f	f	766	Fandrabava	0	0	f		0	f	f	3
711	2	{709,710,712,713}		0	320	t	(2635,862)	t	Sugar	f	f	f	3426	Arikaraka	0	0	f		0	f	f	2
1198	2	{1188,1189,1197,1201,1202}		0	382	f	(2811,2770)	f	Rare Wood	f	f	f	2736	Fandravola	0	0	f		0	f	f	3
635	2	{634,636}		0	370	t	(2380,175)	f	Tea and Coffee	f	f	f	2689	Wokagee	0	0	f		0	f	f	1
133	2	{66,132,134,137,286,288}		0	351	f	(891,895)	t	Salt	f	f	f	4089	Lesliaj	0	0	f		0	f	f	2
296	2	{147,148,149,257,259,295,297,298}		0	329	f	(1271,949)	f	Wine	f	f	f	3723	Kryeliku	0	0	f		0	f	f	3
628	2	{626,627,629,630}		0	352	t	(2333,367)	f	Paper	f	f	f	2840	Llalot	0	0	f		0	f	f	3
68	0	{60,61,67,69}		0	264	f	(722,909)	t	Wool	f	f	f	3759	Xhataj	0	0	f		0	f	f	2
928	0	{927,929,930,931,934,935}		0	253	t	(2725,1280)	t	Wool	f	f	f	4182	Xhycyrë	0	0	f		0	f	f	2
876	0	{875,877,906,907,908}		0	397	t	(3726,416)	f	Wool	f	f	f	4127	Budakovec	0	0	f		0	f	f	2
52	0	{49,51,53,54,63,64,135}		0	375	f	(792,1017)	f	Cotton	f	f	f	3448	Bullajt	0	0	f		0	f	f	2
560	7	{558,559,561,573,590}		0	123	t	(1132,2603)	t	Coal	f	f	f	278	Neuschlag	0	0	f		0	f	f	2
748	2	{745,746,747,749,753}		0	388	f	(3199,241)	f	Grain	f	f	f	3281	Ebreichdeck	0	0	f		0	f	f	2
653	9	{651,652,654,655}		0	181	t	(2713,43)	f	Fish	f	f	f	158	Amdenz	0	0	f		0	f	f	3
1004	0	{966,967,1003,1005,1006,1007}		0	278	f	(3450,1400)	t	Livestock	f	f	f	4391	Hollaweil	0	0	f		0	f	f	2
1116	5	{1112,1115,1117,1118,1119,1120}		0	1016	f	(3112,2073)	f	Copper	f	f	f	758	Lustenstein	0	0	f		0	f	f	4
645	2	{643,644,646,647,648}		0	355	f	(2623,241)	f	Tin	f	f	f	4246	Dornnau	0	0	f		0	f	f	3
688	2	{675,677,687,689,694}		0	360	f	(2889,659)	f	Wine	f	f	f	3066	Ermoulonghi	0	0	f		0	f	f	4
891	2	{877,878,884,886,890,892}		0	341	f	(3922,369)	f	Fruits	f	f	f	3064	Prevedri	0	0	f		0	f	f	4
654	9	{653,655,656,657}		0	154	t	(2734,45)	f	Spices	f	f	f	223	Heravala	0	0	f		0	f	f	2
765	0	{0}		0	365	t	(3493,380)	f	Tea and Coffee	f	f	f	3897	Polipoi	0	0	f		0	f	f	1
1098	0	{940,942,1097,1099,1130,1131,1132,1134}		0	376	f	(2844,1548)	t	Grain	f	f	f	4530	Vavamanitra	0	0	f		0	f	f	1
51	0	{49,50,52,135,136}		0	255	f	(846,1044)	f	Wood	f	f	f	3739	Antsolaona	0	0	f		0	f	f	2
25	0	{23,24,26,27,53}		0	362	f	(749,1123)	f	Fur	f	f	f	4509	Amparatsetra	0	0	f		0	f	f	1
533	0	{531,532,534,598,599,600}		0	324	t	(940,2221)	t	Tea and Coffee	f	f	f	3370	Betatra	0	0	f		0	f	f	3
1040	2	{1023,1024,1039,1041}		0	388	t	(3780,1886)	f	Ivory	f	f	f	3958	Berovombe	0	0	f		0	f	f	1
100	0	{81,82,99,101,104}		0	286	t	(538,740)	f	Wool	f	f	f	3649	Antafolotra	0	0	f		0	f	f	2
63	0	{52,54,61,62,64,66}		0	265	f	(790,952)	t	Tobacco	f	f	f	3971	Vohimavony	0	0	f		0	f	f	1
944	0	{932,943,945,959,960,1097}		0	356	t	(2997,1435)	t	Tobacco	f	f	f	4714	Booriwa	0	0	f		0	f	f	1
1025	2	{1021,1022,1024,1026,1039}		0	347	f	(3918,1782)	f	Livestock	f	f	f	3219	Ceras	0	0	f		0	f	f	1
13	0	{11,12,14,15,16,19}		0	357	t	(670,1276)	f	Livestock	f	f	f	4951	Mamumarë	0	0	f		0	f	f	2
707	0	{690,691,706,708}		0	373	t	(2959,954)	f	Spices	f	f	f	3763	Rrogolenë	0	0	f		0	f	f	1
40	7	{39,41,142}		0	153	t	(1125,1075)	f	Rare Wood	f	f	f	225	Vërkopi	0	0	f		0	f	f	2
1125	7	{1124,1126,1153}		0	122	t	(2844,2054)	f	Glass	f	f	f	278	Livasekë	0	0	f		0	f	f	1
801	2	{751,752,800,803,802}		0	381	t	(3240,126)	f	Fur	f	f	f	4262	Kugjun	0	0	f		0	f	f	1
1180	0	{1167,1171,1179,1181,1190}		0	257	f	(2766,2406)	f	Livestock	f	f	f	4074	Pasekë	0	0	f		0	f	f	2
939	0	{933,934,938,940,941,1136}		0	364	f	(2693,1469)	t	Tobacco	f	f	f	4548	Ansten	0	0	f		0	f	f	1
576	7	{575,577,579,580}		0	172	t	(1028,2812)	t	Glass	f	f	f	151	Götkreis	0	0	f		0	f	f	4
1132	0	{1098,1131,1134,1134,1142,1143}		0	373	f	(2757,1674)	t	Livestock	f	f	f	3811	Altental	0	0	f		0	f	f	1
874	2	{864,865,873,875,877,878}		0	300	f	(3805,295)	f	Salt	f	f	f	2592	Kirchdenz	0	0	f		0	f	f	2
743	2	{742,745,750}		0	328	t	(3121,173)	f	Ivory	f	f	f	3640	Gänsernkirchen	0	0	f		0	f	f	1
977	2	{975,976,978,982,983,984}		0	398	t	(4059,2826)	f	Tin	f	f	f	4237	Floliada	0	0	f		0	f	f	1
318	9	{316,317,319}		0	181	t	(1703,378)	f	Fish	f	f	f	181	Terben	0	0	f		0	f	f	1
986	1	{983,984,985,987,988}		0	167	f	(3988,2987)	f	Paper	f	f	f	724	Metarni	0	0	f		0	f	f	1
1011	0	{999,1000,1001,1010,1012}		0	320	f	(3704,1411)	f	Grain	f	f	f	3634	Vounina	0	0	f		0	f	f	3
971	2	{970,972,973}		0	381	t	(3886,2628)	f	Spices	f	f	f	3293	Edestiada	0	0	f		0	f	f	3
972	2	{971,973,979}		0	352	t	(3892,2752)	f	Livestock	f	f	f	2985	Tsalangwe	0	0	f		0	f	f	1
189	9	{191,192,193}		0	147	f	(1271,277)	f	Spices	f	f	f	180	Mitunte	0	0	f		0	f	f	1
187	9	{186,188,194,195}		0	127	t	(1303,308)	f	Glass	f	f	f	245	Blalaomo	0	0	f		0	f	f	4
283	7	{274,275,281,282,284}		0	166	f	(1017,749)	t	Glass	f	f	f	151	Mponera	0	0	f		0	f	f	1
979	2	{972,973,978,980,981}		0	302	t	(3796,2804)	f	Glass	f	f	f	2938	Limlanje	0	0	f		0	f	f	3
166	0	{165,167,168,476,477,478}		0	335	f	(1541,673)	f	Fur	f	f	f	3175	Ngache	0	0	f		0	f	f	2
984	1	{977,983,985,986}		0	153	t	(4152,2901)	f	Glass	f	f	f	722	Poonbilli	0	0	f		0	f	f	1
791	5	{790,792,793}		0	1021	t	(3428,16)	f	Spices	f	f	f	797	Toko	0	0	f		0	f	f	1
300	0	{162,163,301,302,483}		0	359	t	(1573,497)	f	Tea and Coffee	f	f	f	3923	Šipojaš	0	0	f		0	f	f	4
514	2	{513,515}		0	340	t	(524,1003)	f	Fish	f	f	f	4076	Stijki	0	0	f		0	f	f	2
204	9	{203,205}		0	125	f	(1080,313)	f	Fur	f	f	f	272	Bijeldor	0	0	f		0	f	f	2
135	7	{51,52,64,134,136}		0	161	f	(844,990)	f	Spices	f	f	f	213	Kalengrad	0	0	f		0	f	f	2
983	1	{977,982,984,986,987}		0	129	f	(4014,2946)	f	Ivory	f	f	f	579	Trehać	0	0	f		0	f	f	1
155	0	{154,156,179,234,235,245,246}		0	383	f	(1291,657)	t	Wool	f	f	f	3048	Caska	0	0	f		0	f	f	1
178	0	{157,158,159,160,177,179,180,182}		0	376	f	(1390,529)	f	Tea and Coffee	f	f	f	4268	Sherpenwerpen	0	0	f		0	f	f	2
138	7	{44,47,50,136,137,139}		0	110	f	(938,1021)	f	Coal	f	f	f	207	Dillaas	0	0	f		0	f	f	4
145	0	{144,146,147,255,256}		0	360	t	(1156,1006)	f	Wood	f	f	f	3766	Nieuwport	0	0	f		0	f	f	1
160	0	{159,161,162,176,177,178}		0	382	f	(1444,535)	f	Livestock	f	f	f	4162	Halstraten	0	0	f		0	f	f	3
883	9	{869,881,882}		0	120	t	(4068,106)	f	Fish	f	f	f	299	Torstraten	0	0	f		0	f	f	3
151	0	{150,152,153,248,293,294,295}		0	321	f	(1269,859)	f	Tobacco	f	f	f	4405	Westden	0	0	f		0	f	f	4
153	0	{151,152,154,246,248}		0	324	f	(1267,787)	t	Fruits	f	f	f	4420	Landtals	0	0	f		0	f	f	1
134	7	{64,66,133,135,136}		0	136	f	(859,940)	t	Silk	f	f	f	164	Messimezia	0	0	f		0	f	f	2
1113	5	{1111,1112,1114,1115,1127}		0	1050	f	(3078,1957)	t	Tin	f	f	f	775	Sassarence	0	0	f		0	f	f	3
130	0	{0}		0	285	f	(801,841)	f	Glass	f	f	f	4053	Scabria	0	0	f		0	f	f	2
985	1	{984,986,988}		0	102	t	(4144,2999)	f	Glass	f	f	f	517	Thyochenza	0	0	f		0	f	f	2
1029	0	{1018,1019,1028,1030,1031}		0	280	f	(4059,1578)	f	Spices	f	f	f	4912	Maloji	0	0	f		0	f	f	1
180	2	{178,179,181,182,229,230,235}		0	320	f	(1323,531)	f	Fur	f	f	f	3832	Chitiza	0	0	f		0	f	f	1
889	0	{886,887,888,890,894,895}		0	275	f	(4014,466)	t	Cotton	f	f	f	4094	Chikutete	0	0	f		0	f	f	1
169	5	{168,170,171,474,475}		0	1245	f	(1460,711)	f	Raw Stone	f	f	f	701	Phade	0	0	f		0	f	f	3
194	9	{187,193,195,220}		0	163	f	(1244,324)	f	Ivory	f	f	f	261	Nathenkota	0	0	f		0	f	f	3
195	9	{186,187,194,219,221,220}		0	149	f	(1249,344)	f	Ivory	f	f	f	276	Malaotheche	0	0	f		0	f	f	1
185	9	{184,186,221,222}		0	164	t	(1309,380)	t	Glass	f	f	f	263	Myamine	0	0	f		0	f	f	1
190	9	{191}		0	155	t	(1352,229)	f	Fur	f	f	f	236	Neslavgrad	0	0	f		0	f	f	1
129	2	{127,128,131}		0	306	f	(868,787)	t	Fur	f	f	f	3725	Jazin	0	0	f		0	f	f	1
1064	2	{1061,1062,1063,1065}		0	399	f	(3488,1859)	f	Paper	f	f	f	3631	Viška	0	0	f		0	f	f	3
83	0	{82,84,85,101}		0	349	t	(457,785)	f	Rare Wood	f	f	f	3159	Traboj	0	0	f		0	f	f	3
124	7	{113,120,123,125,126}		0	148	t	(850,562)	t	Coal	f	f	f	209	Čapčac	0	0	f		0	f	f	3
211	2	{200,201,202,210}		0	364	f	(1120,326)	f	Copper	f	f	f	3858	Čedanj	0	0	f		0	f	f	1
216	2	{213,214,217,218}		0	348	t	(1100,439)	f	Rare Wood	f	f	f	2592	Zothout	0	0	f		0	f	f	3
365	0	{362,363,366,367}		0	356	t	(1393,1165)	f	Wood	f	f	f	4468	Milišća	0	0	f		0	f	f	1
887	0	{885,886,888,889,897}		0	394	t	(4068,495)	f	Paper	f	f	f	3881	Dikzen	0	0	f		0	f	f	1
261	5	{258,260,262,294}		0	1149	f	(1352,916)	f	Coal	f	f	f	616	Korteind	0	0	f		0	f	f	2
234	2	{155,231,233,235,236,237,245}		0	358	f	(1244,587)	f	Wine	f	f	f	4277	Oudenhal	0	0	f		0	f	f	1
295	2	{149,150,151,257,294,296}		0	335	f	(1289,909)	f	Salt	f	f	f	4191	Dammuide	0	0	f		0	f	f	1
260	5	{258,259,261,262,266}		0	1215	f	(1370,940)	f	Copper	f	f	f	743	Weststraten	0	0	f		0	f	f	3
291	0	{154,156,157,290,292}		0	361	f	(1359,702)	f	Tea and Coffee	f	f	f	4337	Nieuwschot	0	0	f		0	f	f	1
285	7	{126,128}		0	133	f	(916,733)	f	Coal	f	f	f	207	Lamellino	0	0	f		0	f	f	2
236	2	{234,237,239,245}		0	306	f	(1251,628)	f	Glass	f	f	f	2916	Cagliana	0	0	f		0	f	f	1
275	7	{251,252,274,276,281,283}		0	126	f	(1078,733)	f	Paper	f	f	f	227	Collesaro	0	0	f		0	f	f	1
700	5	{699,701,702,1216}		0	1100	f	(2792,767)	t	Spices	f	f	f	786	Baghetonto	0	0	f		0	f	f	1
925	0	{924}		0	263	t	(3424,1012)	f	Fruits	f	f	f	4697	Xabuto	0	0	f		0	f	f	2
657	9	{654,656,658}		0	197	t	(2772,70)	f	Glass	f	f	f	164	Naputo	0	0	f		0	f	f	1
704	0	{691,703,705,706,709}		0	369	t	(2801,936)	f	Rare Wood	f	f	f	3713	Moatida	0	0	f		0	f	f	1
74	0	{72,73,75,76}		0	257	t	(533,922)	f	Fur	f	f	f	4600	Chikulo	0	0	f		0	f	f	4
351	2	{331,348,352,353}		0	331	t	(1951,475)	f	Salt	f	f	f	4248	Macilacuala	0	0	f		0	f	f	1
577	7	{576,578,579}		0	169	t	(1044,2864)	f	Coal	f	f	f	203	Lilo	0	0	f		0	f	f	1
854	9	{851,852,853,855,856}		0	134	t	(3584,94)	f	Spices	f	f	f	172	Balloundra	0	0	f		0	f	f	1
781	2	{778,779,782}		0	311	t	(3012,55)	f	Livestock	f	f	f	3259	Rakopan	0	0	f		0	f	f	1
93	2	{77,78,86,87,92}		0	304	t	(394,929)	f	Salt	f	f	f	3997	Blagoevski	0	0	f		0	f	f	2
827	5	{817,826,828,834,835}		0	1188	t	(3433,187)	f	Copper	f	f	f	893	Svobol	0	0	f		0	f	f	3
964	0	{954,955,963,965,1092}		0	270	f	(3285,1413)	f	Precious Goods	f	f	f	3857	Provarna	0	0	f		0	f	f	2
923	0	{926}		0	362	t	(3321,810)	f	Glass	f	f	f	3703	Stamvishte	0	0	f		0	f	f	2
599	0	{533,593,594,597,598,600}		0	371	f	(1019,2302)	t	Grain	f	f	f	4872	Kubvo	0	0	f		0	f	f	3
1187	2	{1184,1185,1186,1188,1204}		0	315	t	(3099,2754)	f	Glass	f	f	f	3333	Gabrobrod	0	0	f		0	f	f	1
680	0	{678,679,681,684}		0	366	t	(2662,533)	f	Fur	f	f	f	3724	Alenlet	0	0	f		0	f	f	2
682	0	{681,683,717,718}		0	325	t	(2547,560)	f	Wood	f	f	f	3956	Besanluire	0	0	f		0	f	f	1
908	0	{876,906,907,910,911}		0	332	f	(3694,488)	t	Wool	f	f	f	4101	Martoise	0	0	f		0	f	f	2
543	0	{542,544,545}		0	369	t	(1600,2326)	f	Fruits	f	f	f	3560	Aviçon	0	0	f		0	f	f	3
1178	0	{1172,1176,1177,1179,1190,1191}		0	300	f	(2619,2417)	f	Paper	f	f	f	3637	Bergessonne	0	0	f		0	f	f	2
1214	0	{0}		0	273	t	(3438,2182)	f	Spices	f	f	f	4534	Vierbonne	0	0	f		0	f	f	1
1049	2	{1046,1047,1050,1051,1062}		0	364	f	(3585,1771)	t	Tobacco	f	f	f	2770	Aurigneux	0	0	f		0	f	f	1
1106	5	{1104,1105,1107}		0	1170	f	(3145,1893)	f	Copper	f	f	f	640	Civilerno	0	0	f		0	f	f	1
1146	0	{1145,1147,1152}		0	330	t	(2563,1814)	f	Spices	f	f	f	3641	Cinisto	0	0	f		0	f	f	1
1068	5	{1067,1069,1079,1080}		0	1097	f	(3355,2009)	f	Precious Stones	f	f	f	664	Faersala	0	0	f		0	f	f	2
561	7	{560,562,570,572}		0	116	t	(1206,2637)	t	Rare Wood	f	f	f	229	Modivia	0	0	f		0	f	f	3
119	7	{114,115,10,121,122,123}		0	142	f	(697,551)	t	Coal	f	f	f	268	Xane	0	0	f		0	f	f	3
11	0	{3,10,12,13}		0	263	t	(733,1298)	t	Ivory	f	f	f	4278	Mansano	0	0	f		0	f	f	1
278	7	{232,277}		0	122	t	(1145,562)	f	Paper	f	f	f	162	Mansano	0	0	f		0	f	f	1
1172	0	{1171,1173,1174,1175,1178,1179}		0	315	t	(2628,2277)	f	Wool	f	f	f	3749	Resdica	0	0	f		0	f	f	3
613	1	{583,610,612,614,619,620}		0	169	t	(727,2650)	f	Dyes	f	f	f	785	Monba	0	0	f		0	f	f	4
1209	2	{1210}		0	336	t	(3348,2727)	f	Fur	f	f	f	3319	Nampulimane	0	0	f		0	f	f	1
651	9	{649,650,652,653}		0	134	t	(2644,43)	f	Fur	f	f	f	184	Cooldong	0	0	f		0	f	f	3
400	5	{399,398,401,405,425,462}		0	1129	f	(1748,749)	f	Precious Stones	f	f	f	609	Samovin	0	0	f		0	f	f	1
354	2	{353,355,356}		0	382	t	(1989,549)	f	Spices	f	f	f	4377	Pavlikovski	0	0	f		0	f	f	3
816	2	{808,813,814,815,817,818,819,820}		0	388	t	(3386,157)	f	Grain	f	f	f	2568	Avignan	0	0	f		0	f	f	3
890	0	{886,889,891,892,893,894}		0	251	f	(3967,425)	f	Wood	f	f	f	3832	Angousart	0	0	f		0	f	f	3
933	0	{931,932,934,939,941,942}		0	354	f	(2792,1429)	t	Grain	f	f	f	4125	Narzon	0	0	f		0	f	f	1
149	2	{148,150,249,255,295,296}		0	310	f	(1240,916)	f	Wine	f	f	f	4357	Sarsier	0	0	f		0	f	f	3
320	9	{319,321,323,324,325,326}		0	153	f	(1762,412)	f	Fur	f	f	f	160	Bournoît	0	0	f		0	f	f	2
783	2	{780,782,784}		0	358	t	(3067,42)	f	Wine	f	f	f	2821	Boursier	0	0	f		0	f	f	1
909	0	{0}		0	308	t	(3651,459)	f	Grain	f	f	f	3585	Almacos	0	0	f		0	f	f	2
1137	0	{937,938,1136,1138,1139}		0	330	t	(2588,1499)	f	Wool	f	f	f	3232	Reniche	0	0	f		0	f	f	1
902	0	{895,901,903,904,917,918}		0	386	f	(3890,558)	t	Grain	f	f	f	3867	Guavoa	0	0	f		0	f	f	1
1065	7	{1060,1063,1064,1066,1067,1071}		0	123	t	(3461,1938)	f	Paper	f	f	f	283	Guija	0	0	f		0	f	f	1
1061	2	{1051,1059,1060,1062,1064,1065}		0	362	f	(3526,1886)	f	Paper	f	f	f	2625	Chabezi	0	0	f		0	f	f	2
813	2	{811,812,814,816,820,821}		0	335	f	(3357,130)	f	Livestock	f	f	f	2963	Solengwa	0	0	f		0	f	f	2
623	1	{0}		0	176	t	(88,3078)	f	Glass	f	f	f	689	Lundashi	0	0	f		0	f	f	4
792	5	{790,791,793,794}		0	1169	t	(3389,27)	f	Coal	f	f	f	865	Kabogwe	0	0	f		0	f	f	4
709	0	{703,704,710,711}		0	340	t	(2713,904)	f	Grain	f	f	f	4862	Kawamzongwe	0	0	f		0	f	f	2
822	5	{812,813,821,823}		0	1088	t	(3384,112)	f	Tin	f	f	f	746	Mponlunga	0	0	f		0	f	f	2
46	0	{31,32,34,36,37,45,47,48}		0	266	f	(918,1147)	t	Wool	f	f	f	3492	Zambewezi	0	0	f		0	f	f	1
1196	2	{1189,1190,1191,1195,1197}		0	322	f	(2658,2644)	f	Fur	f	f	f	4297	Caideena	0	0	f		0	f	f	1
915	0	{913,914,916}		0	297	t	(3823,718)	f	Glass	f	f	f	3956	Bremobor	0	0	f		0	f	f	3
1168	5	{1167,1170,1171}		0	1173	t	(2826,2295)	f	Copper	f	f	f	772	Krikovar	0	0	f		0	f	f	2
869	9	{868,870,882,883}		0	159	t	(4003,126)	f	Glass	f	f	f	272	Samorinja	0	0	f		0	f	f	4
799	9	{797,798}		0	159	t	(3643,16)	f	Glass	f	f	f	171	Stovar	0	0	f		0	f	f	3
1019	2	{1018,1020,1027,1028,1029}		0	341	t	(4012,1670)	t	Fish	f	f	f	3723	Vula	0	0	f		0	f	f	1
247	0	{149,243,244,246,248,249,250}		0	267	f	(1213,819)	t	Wood	f	f	f	3347	Kutivača	0	0	f		0	f	f	2
579	7	{576,577,578,580,581}		0	146	t	(961,2799)	f	Paper	f	f	f	230	Orarica	0	0	f		0	f	f	4
1031	0	{1028,1029,1030,1032,1033}		0	378	f	(3938,1533)	t	Grain	f	f	f	3771	Großbruck	0	0	f		0	f	f	3
739	2	{736,737,738,740,741,746}		0	322	f	(3112,295)	t	Tin	f	f	f	3401	Lüdinghöring	0	0	f		0	f	f	2
1148	0	{1147,1150,1151,1152}		0	260	f	(2543,1733)	f	Paper	f	f	f	4445	Elsterbog	0	0	f		0	f	f	4
78	2	{76,77,79,86,93}		0	398	f	(443,916)	f	Glass	f	f	f	2852	Elmroda	0	0	f		0	f	f	1
1082	5	{1078,1079,1080,1081,1111}		0	1251	f	(3195,1969)	f	Silver	f	f	f	634	Gailhude	0	0	f		0	f	f	4
612	1	{583,584,585,610,611,613}		0	141	f	(817,2655)	f	Glass	f	f	f	791	Dillenwig	0	0	f		0	f	f	3
853	9	{849,850,851,854}		0	187	t	(3559,92)	f	Fur	f	f	f	237	Eltershafen	0	0	f		0	f	f	1
1181	0	{1167,1180,1182,1190}		0	290	f	(2858,2516)	f	Wood	f	f	f	3632	Manguache	0	0	f		0	f	f	2
973	2	{970,971,972,974,975,977,978,979}		0	309	f	(3907,2708)	f	Rare Wood	f	f	f	2680	Esmoxa	0	0	f		0	f	f	2
1128	0	{1100,1101,1127,1129,1130}		0	276	t	(2875,1758)	f	Spices	f	f	f	4142	Batejo	0	0	f		0	f	f	2
1063	7	{1062,1064,1065,1071,1072,1073}		0	145	f	(3452,1816)	t	Paper	f	f	f	163	Meamoz	0	0	f		0	f	f	3
740	2	{739,741,742,745,746}		0	312	f	(3127,250)	f	Iron	f	f	f	4081	Maabwe	0	0	f		0	f	f	1
340	5	{336,339,350,352,359}		0	1171	f	(1903,542)	f	Silver	f	f	f	652	Luwinwezi	0	0	f		0	f	f	4
1072	5	{1063,1070,1071,1073,1075}		0	1183	f	(3389,1870)	f	Raw Stone	f	f	f	865	Mpila	0	0	f		0	f	f	2
197	9	{196,198,201}		0	170	t	(1188,263)	f	Glass	f	f	f	262	Sibombwe	0	0	f		0	f	f	2
1012	0	{999,1010,1011,1013,1031,1032,1033,1034}		0	379	f	(3825,1463)	f	Livestock	f	f	f	3062	Lugwi	0	0	f		0	f	f	3
221	2	{185,186,195,219,222,224,225}		0	333	f	(1251,398)	f	Tea and Coffee	f	f	f	3807	Lukusama	0	0	f		0	f	f	1
16	0	{13,15,17,18,19}		0	360	f	(637,1237)	f	Paper	f	f	f	3189	Kapupo	0	0	f		0	f	f	3
1155	5	{1123,1124,1154,1156}		0	1186	t	(3027,2226)	f	Raw Stone	f	f	f	716	Manlang	0	0	f		0	f	f	3
358	2	{335,336,357,359}		0	351	t	(1879,594)	f	Copper	f	f	f	2929	Jezejevec	0	0	f		0	f	f	1
856	9	{852,854,855,857}		0	104	t	(3613,153)	f	Spices	f	f	f	269	Opatilok	0	0	f		0	f	f	1
24	0	{22,23,25,26}		0	257	f	(729,1141)	f	Cotton	f	f	f	4262	Dubropin	0	0	f		0	f	f	1
948	0	{947,949,956,957}		0	256	t	(3193,1285)	f	Glass	f	f	f	3503	Slatizerce	0	0	f		0	f	f	3
329	9	{323,324,328,330,334,343,344}		0	145	f	(1836,434)	f	Glass	f	f	f	214	Bjegrad	0	0	f		0	f	f	2
835	5	{827,834,836}		0	1138	t	(3456,189)	f	Coal	f	f	f	682	Ilorovo	0	0	f		0	f	f	3
1205	2	{1203,1204,1206}		0	321	t	(2946,3110)	f	Glass	f	f	f	4072	Adebog	0	0	f		0	f	f	1
669	0	{667,668,670,671,672,673,676}		0	356	f	(2979,493)	f	Grain	f	f	f	3764	Osterlein	0	0	f		0	f	f	1
1032	0	{1012,1013,1016,1017,1030,1031,1033}		0	273	f	(3942,1485)	t	Precious Goods	f	f	f	3074	Cuxkamp	0	0	f		0	f	f	4
566	5	{564,565,567,569}		0	1031	t	(1219,2788)	f	Raw Stone	f	f	f	687	Romroda	0	0	f		0	f	f	2
1070	5	{1066,1071,1072,1075,1077,1078,1079}		0	1271	f	(3335,1926)	f	Silver	f	f	f	613	Gladenhude	0	0	f		0	f	f	1
1194	2	{1193,1195,1199}		0	329	t	(2297,2729)	f	Livestock	f	f	f	3762	Ersten	0	0	f		0	f	f	2
253	2	{249,250,251,252,254,256,267,289}		0	308	f	(1120,866)	t	Salt	f	f	f	2770	Alsschau	0	0	f		0	f	f	3
642	2	{641,643,646}		0	391	t	(2554,247)	f	Sugar	f	f	f	4418	Trasmo	0	0	f		0	f	f	1
79	2	{75,76,78,80,84,85,86}		0	358	f	(450,866)	f	Salt	f	f	f	2864	Vibos	0	0	f		0	f	f	1
19	0	{12,13,16,18,20,28}		0	356	f	(718,1219)	t	Wool	f	f	f	4350	Camagal	0	0	f		0	f	f	1
730	2	{726,727,728,729,731,732,733}		0	370	f	(3103,418)	t	Wood	f	f	f	3426	Gafarosa	0	0	f		0	f	f	2
92	2	{87,91,93}		0	348	t	(353,929)	f	Tea and Coffee	f	f	f	3158	Lupagani	0	0	f		0	f	f	3
581	5	{579,580,582,584,585}		0	1082	t	(909,2761)	f	Copper	f	f	f	644	Mazoru	0	0	f		0	f	f	1
809	2	{804,805,807,808,810,815}		0	334	f	(3319,178)	f	Iron	f	f	f	4219	Buton	0	0	f		0	f	f	4
594	0	{557,591,593,595,597,599}		0	288	f	(1102,2333)	f	Wool	f	f	f	4701	Gwani	0	0	f		0	f	f	1
953	0	{951,952,954,966,967}		0	397	f	(3415,1348)	t	Wool	f	f	f	4982	Chimanira	0	0	f		0	f	f	3
806	2	{757,758,759,805,807}		0	384	f	(3316,229)	f	Wood	f	f	f	3950	Chakage	0	0	f		0	f	f	2
991	0	{989,990,992,997,1000,1001}		0	262	t	(3702,1260)	f	Spices	f	f	f	4795	Turbawa	0	0	f		0	f	f	1
1185	0	{1182,1183,1184,1186,1187}		0	309	f	(3036,2606)	f	Grain	f	f	f	3552	Sušiles	0	0	f		0	f	f	3
634	2	{635,636,637}		0	321	t	(2443,191)	f	Livestock	f	f	f	4193	Iličani	0	0	f		0	f	f	2
557	7	{555,556,558,591,594,595}		0	136	f	(1120,2432)	f	Rare Wood	f	f	f	253	Vevto	0	0	f		0	f	f	2
916	0	{898,899,913,915,917}		0	396	t	(3879,709)	f	Wood	f	f	f	4745	Skoplesta	0	0	f		0	f	f	3
307	0	{303,306,308,309,480,481,482}		0	390	f	(1609,605)	f	Tea and Coffee	f	f	f	3791	Belmica	0	0	f		0	f	f	3
805	2	{759,804,806,807,809}		0	315	f	(3316,209)	f	Wood	f	f	f	3987	Bikov	0	0	f		0	f	f	1
61	0	{54,55,60,62,63,67,68}		0	386	f	(731,970)	t	Tobacco	f	f	f	4142	Lojašeišta	0	0	f		0	f	f	2
661	0	{659,660,662,663,664}		0	384	t	(2815,331)	f	Wood	f	f	f	4003	Dublee	0	0	f		0	f	f	1
85	5	{79,83,84,86}		0	1116	t	(432,812)	f	Raw Stone	f	f	f	813	Clonkilty	0	0	f		0	f	f	2
823	9	{821,822,824,825,829,830}		0	122	t	(3404,112)	f	Fur	f	f	f	292	Granderry	0	0	f		0	f	f	2
209	2	{208,210,213}		0	308	f	(1071,360)	f	Glass	f	f	f	4333	Tullanard	0	0	f		0	f	f	4
842	5	{837,838,839,843,846,847}		0	1259	f	(3490,146)	f	Gold	f	f	f	746	Tullahal	0	0	f		0	f	f	4
1024	2	{1022,1023,1025,1039,1040}		0	395	f	(3888,1827)	t	Chocolate	f	f	f	2681	Newney	0	0	f		0	f	f	4
454	2	{375,376,455,456}		0	320	t	(1735,949)	f	Livestock	f	f	f	2616	Dunford	0	0	f		0	f	f	2
1005	0	{965,966,969,1004,1006,1093}		0	383	f	(3387,1452)	t	Wood	f	f	f	3572	Cavila	0	0	f		0	f	f	3
1171	0	{1167,1668,1172,1179,1180}		0	266	t	(2712,2322)	f	Cotton	f	f	f	4204	Guarcia	0	0	f		0	f	f	1
1204	2	{1187,1188,1202,1203,1205,1206}		0	331	t	(2988,2874)	f	Paper	f	f	f	2970	Galirez	0	0	f		0	f	f	2
988	1	{985,986,987}		0	179	t	(3942,3090)	f	Ivory	f	f	f	595	Ávirón	0	0	f		0	f	f	1
70	0	{58,59,60,69,71,72,73}		0	377	f	(616,927)	f	Spices	f	f	f	4850	Penhati	0	0	f		0	f	f	1
1120	7	{1115,1116,1119,1121,1122,1123}		0	170	t	(3110,2115)	t	Paper	f	f	f	289	Bindugora	0	0	f		0	f	f	1
1133	0	{1132,1134,1135,1141,1142}		0	303	f	(2745,1627)	t	Cotton	f	f	f	4351	Chitunwayo	0	0	f		0	f	f	2
1207	2	{1208}		0	335	t	(3319,2945)	f	Tea and Coffee	f	f	f	3530	Gopanzi	0	0	f		0	f	f	1
864	2	{860,861,863,865,866,874,875}		0	372	f	(3780,247)	f	Salt	f	f	f	3240	Goni	0	0	f		0	f	f	3
1051	2	{1049,1050,1052,1059,1061,1062}		0	339	f	(3558,1875)	f	Livestock	f	f	f	4281	Shamdu	0	0	f		0	f	f	1
724	0	{671,672,723,725,727,728}		0	293	f	(3098,506)	t	Cotton	f	f	f	4900	Marondera	0	0	f		0	f	f	3
931	0	{928,930,932,933,934}		0	319	t	(2824,1359)	t	Fruits	f	f	f	4225	Gooneragan	0	0	f		0	f	f	2
212	2	{207,208,213,214}		0	376	t	(1039,430)	f	Salt	f	f	f	4012	Dojrovo	0	0	f		0	f	f	3
615	1	{606,607,614,616,619}		0	170	f	(797,2518)	f	Dyes	f	f	f	606	Poja	0	0	f		0	f	f	1
605	2	{601,604,606,607}		0	368	f	(841,2421)	t	Livestock	f	f	f	2607	Zabar	0	0	f		0	f	f	3
901	0	{895,899,900,902,917}		0	355	f	(3935,637)	t	Paper	f	f	f	3993	Velša	0	0	f		0	f	f	2
38	0	{37,39,42}		0	288	t	(1093,1152)	f	Glass	f	f	f	4085	Krivotovo	0	0	f		0	f	f	2
572	5	{561,570,571}		0	1252	f	(1154,2659)	f	Copper	f	f	f	759	Brvenijusa	0	0	f		0	f	f	4
961	0	{958,959,960,962,1090,1091,1094}		0	390	f	(3128,1497)	f	Cotton	f	f	f	4999	Macgar	0	0	f		0	f	f	3
37	0	{36,38,42,43,45,46}		0	263	t	(1017,1127)	f	Wool	f	f	f	3874	Clonakee	0	0	f		0	f	f	4
246	0	{153,154,155,244,245,247,248}		0	387	f	(1249,747)	t	Wool	f	f	f	3796	Maccommon	0	0	f		0	f	f	1
681	0	{680,682,683,684}		0	313	t	(2610,553)	f	Livestock	f	f	f	4046	Shanway	0	0	f		0	f	f	2
1007	0	{1002,1003,1004,1006,1008}		0	398	f	(3499,1449)	f	Glass	f	f	f	4351	Castlegheda	0	0	f		0	f	f	3
1124	7	{1123,1125,1126,1153,1155}		0	123	f	(2977,2109)	t	Silk	f	f	f	168	Naran	0	0	f		0	f	f	1
41	7	{39,40,42,43,44,142}		0	112	f	(1075,1069)	f	Paper	f	f	f	174	Dubtowel	0	0	f		0	f	f	4
102	2	{97,99,103,104,105}		0	346	f	(628,776)	t	Sugar	f	f	f	2690	Raelellón	0	0	f		0	f	f	1
165	0	{164,166,167,478,480,481}		0	306	f	(1539,641)	t	Wool	f	f	f	3153	Márrol	0	0	f		0	f	f	1
172	5	{158,168,170,173,175}		0	1270	f	(1467,661)	f	Silver	f	f	f	713	Seria	0	0	f		0	f	f	3
293	2	{151,152,294,415}		0	323	f	(1321,801)	f	Salt	f	f	f	4301	Orova	0	0	f		0	f	f	2
571	5	{569,570,572}		0	1192	f	(1170,2707)	f	Silver	f	f	f	878	Vaceni	0	0	f		0	f	f	2
252	2	{251,253,274,289}		0	381	f	(1078,835)	f	Fruits	f	f	f	4295	Doroteşti	0	0	f		0	f	f	1
701	5	{693,700,702}		0	1184	f	(2811,765)	f	Raw Stone	f	f	f	853	Gioba	0	0	f		0	f	f	1
343	5	{329,334,344}		0	1083	f	(1849,481)	f	Tin	f	f	f	772	Târrest	0	0	f		0	f	f	4
912	0	{910,911,913,914}		0	299	t	(3730,637)	f	Livestock	f	f	f	4831	Cernarşa	0	0	f		0	f	f	1
227	2	{224,225,226,228,233,232}		0	352	f	(1210,520)	f	Chocolate	f	f	f	4384	Piterşa	0	0	f		0	f	f	3
918	0	{902,904,913,917}		0	343	f	(3850,569)	t	Wood	f	f	f	4710	Conmon	0	0	f		0	f	f	1
302	0	{300,301,303,304,315}		0	372	t	(1604,481)	f	Wood	f	f	f	3547	Amersdaal	0	0	f		0	f	f	3
328	9	{324,327,329,330}		0	117	t	(1849,389)	f	Glass	f	f	f	231	Zoetermegen	0	0	f		0	f	f	2
342	5	{338,341,344,346,350}		0	1126	f	(1874,493)	f	Raw Stone	f	f	f	849	Staventer	0	0	f		0	f	f	1
80	2	{75,79,81,82,84,98}		0	337	f	(488,855)	t	Paper	f	f	f	3029	Devenberg	0	0	f		0	f	f	1
112	2	{109,111,114,115}		0	385	f	(702,697)	f	Copper	f	f	f	2620	Dierburg	0	0	f		0	f	f	4
671	0	{669,670,672,724,728}		0	343	f	(3026,526)	f	Sugar	f	f	f	3991	Asren	0	0	f		0	f	f	1
1042	2	{1037,1038,1041,1043,1047,1048}		0	344	f	(3751,1733)	t	Livestock	f	f	f	3331	Valejón	0	0	f		0	f	f	2
97	0	{95,96,98,99,102,105,107}		0	347	f	(619,821)	t	Sugar	f	f	f	3471	Zamovia	0	0	f		0	f	f	1
1055	2	{1053,1054,1056}		0	354	t	(3697,2128)	f	Tea and Coffee	f	f	f	3619	Zastela	0	0	f		0	f	f	3
893	0	{890,892,894,803,804}		0	283	f	(3901,477)	t	Fur	f	f	f	4996	Riorez	0	0	f		0	f	f	4
1136	0	{938,939,940,1135,1137,1139,1140}		0	295	f	(2653,1537)	t	Paper	f	f	f	4513	Balgăşani	0	0	f		0	f	f	1
272	0	{269,270,271,273}		0	359	f	(981,907)	t	Paper	f	f	f	3591	Panteghetu	0	0	f		0	f	f	1
117	2	{116,118}		0	311	t	(623,623)	f	Tobacco	f	f	f	3655	Bârftea	0	0	f		0	f	f	1
1203	2	{1202,1204,1205}		0	326	t	(2831,3020)	f	Sugar	f	f	f	2545	Timirad	0	0	f		0	f	f	1
123	7	{119,120,122,124}		0	133	t	(792,515)	t	Paper	f	f	f	187	Buhuşiţa	0	0	f		0	f	f	1
439	1	{438,440,465}		0	118	t	(2068,1476)	f	Paper	f	f	f	658	Fetegalia	0	0	f		0	f	f	4
1140	0	{1135,1136,1139,1141,1149}		0	334	f	(2635,1611)	t	Livestock	f	f	f	3140	Slojud	0	0	f		0	f	f	1
66	0	{62,63,64,67,133,134}		0	399	f	(803,920)	f	Wool	f	f	f	3314	Amerskerk	0	0	f		0	f	f	1
616	2	{604,606,615,617,618,619}		0	349	t	(724,2473)	f	Grain	f	f	f	4302	Ashuizen	0	0	f		0	f	f	1
1199	2	{1194,1195,1200}		0	398	t	(2349,2838)	f	Glass	f	f	f	3535	Slolo	0	0	f		0	f	f	3
128	2	{126,127,129,285}		0	334	f	(891,758)	t	Paper	f	f	f	2836	Amstelstadt	0	0	f		0	f	f	2
170	5	{168,169,171,172}		0	1292	f	(1460,686)	f	Salt	f	f	f	795	Emmelzaal	0	0	f		0	f	f	3
289	2	{262,264,265,266,369,370,386,463}		0	336	f	(1420,927)	f	Paper	f	f	f	3526	Ashof	0	0	f		0	f	f	2
142	7	{41,44,140,141,143,144}		0	120	f	(1051,1037)	f	Coal	f	f	f	208	Knjazamane	0	0	f		0	f	f	2
257	5	{258,259,294,295,296}		0	1026	f	(1325,929)	f	Copper	f	f	f	698	Stanirig	0	0	f		0	f	f	2
87	5	{86,88,90,91,92,93}		0	1152	f	(387,859)	f	Iron	f	f	f	847	Konica	0	0	f		0	f	f	3
927	0	{928,935,936}		0	337	t	(2626,1271)	t	Grain	f	f	f	4605	Arankinda	0	0	f		0	f	f	1
611	5	{585,586,588,610,612}		0	1293	f	(900,2646)	f	Tin	f	f	f	712	Panzar	0	0	f		0	f	f	3
950	0	{949,951,952}		0	367	t	(3323,1264)	f	Wool	f	f	f	4155	Šavor	0	0	f		0	f	f	2
815	2	{808,809,810,814,816}		0	390	f	(3348,166)	f	Paper	f	f	f	2806	Granovci	0	0	f		0	f	f	1
859	9	{857,858,860,861,862}		0	161	t	(3715,142)	f	Fur	f	f	f	197	Laustätten	0	0	f		0	f	f	1
12	0	{10,11,13,19,28}		0	291	f	(738,1255)	t	Cotton	f	f	f	4203	Wädensberg	0	0	f		0	f	f	2
1022	2	{1021,1023,1024,1025}		0	357	t	(3958,1908)	t	Salt	f	f	f	3864	Kreuzstein	0	0	f		0	f	f	1
1191	0	{1177,1178,1190,1192,1193,1195,1196}		0	325	f	(2550,2577)	f	Wood	f	f	f	4964	Opthal	0	0	f		0	f	f	3
1003	0	{967,968,990,1002,1004,1007}		0	341	f	(3524,1409)	f	Wool	f	f	f	4252	Opnacht	0	0	f		0	f	f	2
563	7	{562,564}		0	168	t	(1314,2702)	f	Paper	f	f	f	208	Friseen	0	0	f		0	f	f	3
626	2	{627,628}		0	378	t	(2313,351)	f	Ivory	f	f	f	3478	Freienbach	0	0	f		0	f	f	1
511	2	{512}		0	346	t	(565,1107)	f	Livestock	f	f	f	2914	Kragudište	0	0	f		0	f	f	2
886	2	{884,885,887,889,890,891}		0	361	f	(4021,427)	f	Ivory	f	f	f	3027	Belvor	0	0	f		0	f	f	1
935	0	{927,928,934,936}		0	357	f	(2691,1354)	t	Wool	f	f	f	3070	Novac	0	0	f		0	f	f	1
907	0	{876,906,908}		0	322	f	(3753,488)	f	Wood	f	f	f	3414	Arirug	0	0	f		0	f	f	1
679	0	{665,680}		0	294	t	(2707,492)	f	Paper	f	f	f	4275	Aramane	0	0	f		0	f	f	3
833	5	{828,832,834}		0	1052	f	(3456,153)	f	Salt	f	f	f	866	Panrig	0	0	f		0	f	f	4
1050	2	{1041,1047,1049,1051,1052,1053,1054}		0	334	t	(3650,1863)	f	Livestock	f	f	f	2690	Reilach	0	0	f		0	f	f	1
1114	5	{1113,1115,1126,1127}		0	1068	f	(3022,1994)	t	Copper	f	f	f	697	Laufenkon	0	0	f		0	f	f	1
583	1	{582,584,612,613}		0	142	t	(745,2704)	f	Paper	f	f	f	664	Herneuve	0	0	f		0	f	f	1
1119	7	{1080,1116,1118,1120}		0	173	f	(3180,2106)	t	Silk	f	f	f	268	Menbon	0	0	f		0	f	f	1
42	0	{37,38,39,41,42}		0	328	f	(1082,1098)	f	Paper	f	f	f	3361	Steffisborn	0	0	f		0	f	f	1
771	0	{0}		0	251	t	(3369,496)	f	Wool	f	f	f	4762	Ostermance	0	0	f		0	f	f	2
798	9	{795,796,797,799}		0	103	t	(3635,22)	f	Fur	f	f	f	281	Ergen	0	0	f		0	f	f	2
94	0	{72,75,80,95,98}		0	355	f	(574,864)	t	Livestock	f	f	f	4811	Dravovica	0	0	f		0	f	f	2
322	9	{317,321,332,333}		0	130	f	(1735,450)	f	Fur	f	f	f	241	Konice	0	0	f		0	f	f	1
15	0	{13,14,16,17}		0	306	t	(621,1249)	f	Glass	f	f	f	4083	Črnolavž	0	0	f		0	f	f	4
751	2	{750,752,801}		0	309	t	(3213,142)	f	Fruits	f	f	f	2856	Trbojice	0	0	f		0	f	f	1
866	9	{860,864,865,867,871}		0	142	t	(3854,164)	f	Fish	f	f	f	210	Murskem	0	0	f		0	f	f	4
125	7	{124,126,433}		0	146	t	(891,601)	t	Glass	f	f	f	265	Rogaje	0	0	f		0	f	f	2
760	1	{0}		0	121	t	(2431,1384)	f	Glass	f	f	f	528	Beltinci	0	0	f		0	f	f	1
98	0	{80,81,94,95,97,99}		0	358	f	(558,832)	t	Fruits	f	f	f	3981	Spojba	0	0	f		0	f	f	2
191	9	{189,190,192}		0	114	t	(1314,216)	f	Fish	f	f	f	204	Jerice	0	0	f		0	f	f	1
608	2	{598,590,592,601,607,609}		0	355	f	(976,2450)	f	Chocolate	f	f	f	3169	Noše	0	0	f		0	f	f	1
609	2	{588,589,607,608,610,615}		0	388	f	(880,2520)	f	Wood	f	f	f	3838	Mujana	0	0	f		0	f	f	2
639	9	{637,638,640}		0	112	t	(2387,79)	f	Precious Goods	f	f	f	253	Ratina	0	0	f		0	f	f	1
8	0	{5,6,9,33,35}		0	390	t	(936,1258)	f	Livestock	f	f	f	4439	Jagogaška	0	0	f		0	f	f	1
620	1	{613,618,619}		0	123	t	(666,2576)	f	Fish	f	f	f	754	Kongehus	0	0	f		0	f	f	2
336	5	{335,337,339,340,358,359}		0	1192	f	(1874,558)	f	Raw Stone	f	f	f	627	Skjoldbæk	0	0	f		0	f	f	4
441	1	{442}		0	138	t	(1795,1523)	f	Ivory	f	f	f	784	Vejlev	0	0	f		0	f	f	2
996	0	{992,995,997,998}		0	310	t	(3873,1265)	f	Ivory	f	f	f	4099	Guldhus	0	0	f		0	f	f	2
298	2	{259,296,297,299,484}		0	394	f	(1307,983)	f	Ivory	f	f	f	2904	Dybborg	0	0	f		0	f	f	4
344	5	{329,330,342,343,345,346}		0	1167	f	(1861,463)	f	Salt	f	f	f	777	Smedestrup	0	0	f		0	f	f	2
259	5	{257,258,260,266,298,296,484}		0	1000	f	(1345,965)	f	Iron	f	f	f	803	Karlsborg	0	0	f		0	f	f	1
990	0	{968,989,991,1001,1002,1003}		0	275	f	(3636,1292)	f	Cotton	f	f	f	4019	Fladbæk	0	0	f		0	f	f	3
703	2	{691,692,702,704,709,710}		0	396	f	(2819,832)	t	Glass	f	f	f	3288	Vestergård	0	0	f		0	f	f	1
229	2	{180,223,228,230,231,235}		0	356	f	(1312,540)	t	Fur	f	f	f	3531	Vindholt	0	0	f		0	f	f	4
733	2	{729,730,732,734,737,738}		0	322	f	(3103,349)	t	Ivory	f	f	f	2799	Halrup	0	0	f		0	f	f	2
120	7	{113,114,119,123,124}		0	128	f	(772,612)	t	Rare Wood	f	f	f	157	Kirkehus	0	0	f		0	f	f	2
208	2	{207,209,212,213}		0	303	f	(1057,369)	f	Fur	f	f	f	2664	Tubbokaye	0	0	f		0	f	f	1
312	2	{305,310,313,314,429,430}		0	324	f	(1696,547)	f	Chocolate	f	f	f	4266	Kalintsa	0	0	f		0	f	f	2
532	0	{530,531,533,600,602}		0	267	t	(884,2266)	t	Fruits	f	f	f	4218	Pizhany	0	0	f		0	f	f	2
497	1	{495,496}		0	175	t	(1136,1294)	f	Glass	f	f	f	507	Zhytkakaw	0	0	f		0	f	f	3
540	0	{538,539,547,548,549}		0	311	f	(1370,2239)	f	Wool	f	f	f	4855	Vesterkilde	0	0	f		0	f	f	2
817	5	{816,818,826,827}		0	1087	t	(3409,198)	f	Copper	f	f	f	863	Birkestrup	0	0	f		0	f	f	3
297	2	{146,147,296,298,299}		0	303	t	(1269,1006)	f	Salt	f	f	f	3859	Enshus	0	0	f		0	f	f	1
163	0	{161,162,164,300,483}		0	392	f	(1543,551)	t	Livestock	f	f	f	3776	Lillerup	0	0	f		0	f	f	1
1066	5	{1065,1067,1070,1071}		0	1118	f	(3415,1980)	f	Salt	f	f	f	629	Møllerup	0	0	f		0	f	f	4
719	0	{674,720,721,722}		0	250	t	(3136,643)	f	Fish	f	f	f	4452	Strandstrup	0	0	f		0	f	f	2
993	0	{992,994}		0	386	t	(3793,1215)	f	Fur	f	f	f	3189	Guldskov	0	0	f		0	f	f	1
1027	2	{1019,1020,1026,1028}		0	389	f	(3929,1717)	t	Copper	f	f	f	4494	Silkeholt	0	0	f		0	f	f	1
1154	5	{1124,1153,1155,1156,1169}		0	1192	f	(2941,2212)	f	Tin	f	f	f	621	Rødhavn	0	0	f		0	f	f	2
592	2	{590,591,593,593,601,608}		0	325	f	(1033,2439)	f	Salt	f	f	f	2799	Karlsbæk	0	0	f		0	f	f	3
32	0	{30,31,33,34,46}		0	360	f	(871,1210)	t	Wool	f	f	f	3001	Bjørnbæk	0	0	f		0	f	f	1
39	0	{38,40,41,42}		0	356	t	(1138,1123)	f	Grain	f	f	f	3828	Rødkilde	0	0	f		0	f	f	1
325	9	{319,320,326}		0	184	t	(1773,382)	f	Glass	f	f	f	236	Vitsyezyr	0	0	f		0	f	f	2
1100	0	{1096,1099,1101,1128,1130}		0	376	f	(2923,1686)	f	Cotton	f	f	f	3537	Skitrykaw	0	0	f		0	f	f	2
969	0	{965,1005,1006,1093}		0	380	t	(3364,1521)	t	Glass	f	f	f	4020	Shchusna	0	0	f		0	f	f	2
461	2	{373,374,396,397,298,458,460,462}		0	341	t	(1687,799)	f	Tin	f	f	f	3472	Navapotsavichy	0	0	f		0	f	f	4
348	5	{351,352}		0	1018	f	(1930,504)	f	Raw Stone	f	f	f	713	Narostavy	0	0	f		0	f	f	1
766	0	{767}		0	252	t	(3418,347)	f	Precious Goods	f	f	f	3302	Tammme	0	0	f		0	f	f	2
519	2	{518,522}		0	398	t	(274,1966)	f	Fur	f	f	f	3790	Tamvi	0	0	f		0	f	f	1
878	2	{872,873,874,877,879,884,891}		0	361	f	(3906,315)	f	Rare Wood	f	f	f	4438	Vilsi	0	0	f		0	f	f	4
81	0	{80,82,98,99,100}		0	256	f	(522,796)	f	Grain	f	f	f	4072	Pärpina	0	0	f		0	f	f	3
1159	0	{1158,1160,1161,1162}		0	288	t	(3060,2397)	f	Fur	f	f	f	3032	Kärva	0	0	f		0	f	f	1
157	0	{156,158,179,178,290,291}		0	346	f	(1372,612)	t	Cotton	f	f	f	3444	Kiviõtu	0	0	f		0	f	f	1
1215	5	{698,715,1216,1217}		0	1182	f	(2741,752)	f	Salt	f	f	f	747	Räru	0	0	f		0	f	f	1
981	1	{978,979,980,982,987}		0	168	t	(3807,2912)	f	Precious Goods	f	f	f	531	Kärpina	0	0	f		0	f	f	1
1216	5	{698,699,700,702,1215,1217}		0	1164	f	(2770,783)	f	Copper	f	f	f	608	Otesuu	0	0	f		0	f	f	1
976	2	{975,977}		0	384	t	(4122,2774)	f	Salt	f	f	f	4383	Kaldi	0	0	f		0	f	f	1
1001	0	{990,991,1000,1002,1010,1011}		0	280	f	(3643,1355)	f	Paper	f	f	f	3495	Kiviõna	0	0	f		0	f	f	1
975	2	{973,974,976,977}		0	356	t	(4076,2736)	f	Fish	f	f	f	3648	Kargeva	0	0	f		0	f	f	2
987	1	{981,982,983,986,988}		0	112	t	(3863,2975)	f	Paper	f	f	f	658	Litště	0	0	f		0	f	f	1
804	2	{759,800,803,805,809}		0	312	f	(3303,175)	f	Fruits	f	f	f	3895	Kobíč	0	0	f		0	f	f	2
617	0	{528,603,604,616}		0	300	t	(713,2394)	f	Wool	f	f	f	3024	Těkolov	0	0	f		0	f	f	2
591	2	{557,558,590,592,593,594}		0	329	f	(1087,2446)	f	Iron	f	f	f	2891	Valapa	0	0	f		0	f	f	1
831	5	{829,830,832,840}		0	1055	t	(3440,124)	f	Iron	f	f	f	614	Palde	0	0	f		0	f	f	4
84	5	{79,80,82,83,85}		0	1129	f	(461,837)	f	Gold	f	f	f	761	Sinsa	0	0	f		0	f	f	1
595	0	{553,555,557,594,596,597}		0	269	f	(1147,2329)	f	Tobacco	f	f	f	3736	Räpila	0	0	f		0	f	f	1
524	2	{521,522,523,525,526}		0	332	t	(425,2113)	f	Iron	f	f	f	2569	Karski	0	0	f		0	f	f	1
570	5	{561,562,565,569,571,572}		0	1056	f	(1229,2716)	f	Tin	f	f	f	679	Karngi	0	0	f		0	f	f	4
872	2	{870,871,873,878,879,880}		0	338	f	(3958,256)	f	Grain	f	f	f	4373	Põllin	0	0	f		0	f	f	2
780	2	{779,782,783,784}		0	324	t	(3066,77)	f	Sugar	f	f	f	3471	Kurepää	0	0	f		0	f	f	3
1102	7	{1088,1095,1101,1103,1104,1107,1108}		0	115	f	(3036,1719)	f	Paper	f	f	f	237	Kiviõsalu	0	0	f		0	f	f	2
474	2	{169,171,290,292,417,434,475,516}		0	345	f	(1426,736)	f	Wood	f	f	f	2634	Abgeva	0	0	f		0	f	f	4
896	0	{888,895,897,899,900}		0	271	f	(4036,623)	f	Tea and Coffee	f	f	f	3373	Narme	0	0	f		0	f	f	2
759	2	{752,753,758,800,804,805,806}		0	393	f	(3278,184)	f	Wood	f	f	f	2516	Tajandi	0	0	f		0	f	f	3
676	0	{666,667,669,673,675,677}		0	382	f	(2905,533)	f	Cotton	f	f	f	3490	Rapli	0	0	f		0	f	f	1
633	2	{631,632}		0	335	t	(2473,349)	f	Tea and Coffee	f	f	f	4213	Uhernec	0	0	f		0	f	f	4
954	0	{951,953,955,964,965,966}		0	336	f	(3341,1363)	f	Fruits	f	f	f	3439	Valabem	0	0	f		0	f	f	3
48	0	{27,30,31,46,47,49}		0	334	f	(873,1147)	f	Rare Wood	f	f	f	3234	Hrakov	0	0	f		0	f	f	4
636	2	{635,634,637,638}		0	311	t	(2396,146)	f	Fruits	f	f	f	3285	Kroměkolov	0	0	f		0	f	f	3
906	0	{876,877,904,905,907,908,911}		0	322	f	(3789,472)	f	Glass	f	f	f	3497	Chomusou	0	0	f		0	f	f	2
231	2	{228,229,233,234,335}		0	399	f	(1260,556)	f	Salt	f	f	f	2744	Mänranta	0	0	f		0	f	f	2
1177	0	{1175,1176,1178,1191,1192}		0	252	f	(2469,2496)	f	Paper	f	f	f	4866	Ähtäkumpu	0	0	f		0	f	f	2
168	0	{167,168,170,172,475,476}		0	381	f	(1487,684)	f	Tea and Coffee	f	f	f	4489	Juanni	0	0	f		0	f	f	1
758	2	{753,754,755,757,759,706}		0	331	f	(3287,245)	f	Ivory	f	f	f	4145	Kuripunki	0	0	f		0	f	f	3
562	7	{561,563,564,565,570}		0	168	t	(1260,2646)	t	Silk	f	f	f	258	Juanttinen	0	0	f		0	f	f	3
602	0	{529,530,532,600,601,603,604}		0	343	f	(848,2326)	t	Precious Goods	f	f	f	3484	Kokekola	0	0	f		0	f	f	1
1202	2	{1188,1198,1201,1203,1204}		0	395	t	(2713,2977)	f	Fur	f	f	f	3048	Keusämäki	0	0	f		0	f	f	3
882	9	{869,870,880,881,883}		0	190	f	(4066,169)	f	Fur	f	f	f	289	Kitali	0	0	f		0	f	f	1
472	0	{470,471,490,492,493}		0	358	t	(1215,1377)	f	Grain	f	f	f	3239	Pietarni	0	0	f		0	f	f	2
505	5	{496,498,499,504,506}		0	1060	f	(1201,1285)	f	Tin	f	f	f	799	Balota	0	0	f		0	f	f	3
111	2	{109,110,112,115,116}		0	373	f	(679,682)	f	Tobacco	f	f	f	3295	Töson	0	0	f		0	f	f	1
427	0	{424,426,428,430,432}		0	343	t	(1818,657)	f	Fruits	f	f	f	4488	Szartak	0	0	f		0	f	f	4
476	2	{166,167,168,475,477,516}		0	362	f	(1519,702)	f	Wine	f	f	f	4472	Lajojosmizse	0	0	f		0	f	f	1
203	9	{202,204,205}		0	134	t	(1082,292)	f	Fur	f	f	f	228	Oroszna	0	0	f		0	f	f	2
429	0	{310,311,312,423,428,430}		0	318	f	(1730,639)	f	Tea and Coffee	f	f	f	3091	Riihivalta	0	0	f		0	f	f	1
251	2	{242,250,252,253,275,276}		0	372	f	(1100,794)	f	Ivory	f	f	f	3561	Orimamäki	0	0	f		0	f	f	4
57	0	{23,54,56,58}		0	364	t	(601,1019)	t	Glass	f	f	f	3073	Valkeani	0	0	f		0	f	f	2
69	0	{60,68,70,71}		0	389	f	(693,893)	t	Paper	f	f	f	4943	Huisuu	0	0	f		0	f	f	3
303	0	{301,302,304,306,307,482}		0	353	f	(1624,515)	f	Spices	f	f	f	3619	Nosiä	0	0	f		0	f	f	3
356	2	{353,354,355,357,359}		0	323	t	(1975,580)	f	Tea and Coffee	f	f	f	4204	Ylövala	0	0	f		0	f	f	1
361	0	{360,387,443,444}		0	335	f	(1456,1327)	f	Wool	f	f	f	4852	Niniemi	0	0	f		0	f	f	1
177	2	{160,176,178,182,183}		0	346	t	(1431,468)	t	Tea and Coffee	f	f	f	3647	Haniemi	0	0	f		0	f	f	2
371	1	{369,370,372,376,378,383}		0	118	f	(1532,911)	f	Glass	f	f	f	625	Raaseko	0	0	f		0	f	f	1
391	5	{372,390,392,418,419}		0	1200	f	(1552,819)	f	Silver	f	f	f	809	Raittinen	0	0	f		0	f	f	1
544	1	{543,545}		0	173	t	(1629,2385)	f	Fish	f	f	f	712	Kanttila	0	0	f		0	f	f	3
372	1	{370,371,373,376,389,390,391,392}		0	154	f	(1552,857)	f	Spices	f	f	f	619	Ulranta	0	0	f		0	f	f	1
425	0	{400,403,404,405,406,422,423,424,436}		0	372	f	(1744,704)	t	Rare Wood	f	f	f	3873	Kiskunta	0	0	f		0	f	f	1
245	0	{155,234,2346,239,244,246}		0	389	f	(1267,650)	f	Paper	f	f	f	3947	Ylöpula	0	0	f		0	f	f	2
402	5	{401,403,426,462}		0	1219	t	(1802,727)	f	Iron	f	f	f	644	Heissa	0	0	f		0	f	f	1
388	5	{370,389,463,485}		0	1157	f	(1507,884)	f	Salt	f	f	f	650	Keszna	0	0	f		0	f	f	1
202	9	{201,203,211}		0	101	t	(1127,292)	f	Fur	f	f	f	254	Tatak	0	0	f		0	f	f	4
385	1	{364,381,382,384,386,445}		0	107	f	(1514,1186)	f	Glass	f	f	f	656	Karnor	0	0	f		0	f	f	4
384	1	{363,364,366,383,383,385}		0	140	f	(1444,1105)	f	Glass	f	f	f	776	Szenbóvár	0	0	f		0	f	f	1
428	0	{423,424,426,427,429,430}		0	255	f	(1768,648)	f	Fur	f	f	f	4927	Hólhólmur	0	0	f		0	f	f	1
396	5	{395,397,461}		0	1173	f	(1660,812)	f	Spices	f	f	f	847	Mosfellssós	0	0	f		0	f	f	1
851	9	{845,846,850,852,853,854}		0	121	f	(3546,130)	f	Fur	f	f	f	151	Reykvöllur	0	0	f		0	f	f	1
494	1	{493,495,496}		0	158	t	(1147,1352)	f	Paper	f	f	f	585	Hvolsfjörður	0	0	f		0	f	f	3
410	5	{408,409,411,412,420}		0	1011	f	(1642,778)	f	Precious Stones	f	f	f	851	Keflajahlíð	0	0	f		0	f	f	1
411	5	{395,409,410,412}		0	1057	f	(1658,794)	f	Iron	f	f	f	662	Grundarsker	0	0	f		0	f	f	1
480	2	{165,307,478,479,481}		0	353	f	(1575,646)	f	Chocolate	f	f	f	3002	Blönnarnes	0	0	f		0	f	f	3
265	5	{264,289,386,415,485}		0	1108	f	(1451,900)	f	Precious Stones	f	f	f	607	Eyrarjarhverfi	0	0	f		0	f	f	1
373	1	{372,374,375,376,451}		0	179	f	(1606,846)	f	Paper	f	f	f	639	Þórsnesi	0	0	f		0	f	f	4
405	5	{399,400,406,407,425}		0	1139	f	(1719,749)	f	Salt	f	f	f	775	Dalnes	0	0	f		0	f	f	1
1110	5	{1107,1109,1127}		0	1143	f	(3087,1922)	f	Copper	f	f	f	835	Garðaseyri	0	0	f		0	f	f	4
143	7	{142,144}		0	112	f	(1098,1030)	f	Coal	f	f	f	187	Dalkrókur	0	0	f		0	f	f	2
775	2	{773,774,776,777}		0	382	t	(2998,171)	f	Livestock	f	f	f	4099	Comspol	0	0	f		0	f	f	2
456	2	{375,454,455,457,458}		0	373	f	(1768,925)	f	Spices	f	f	f	3845	Strănești	0	0	f		0	f	f	1
446	0	{380,381,445,447}		0	337	t	(1620,1231)	f	Wool	f	f	f	3626	Rîșcamenca	0	0	f		0	f	f	3
516	2	{419,434,474,475,476,477}		0	357	f	(1505,745)	t	Spices	f	f	f	3528	Străză	0	0	f		0	f	f	1
5	0	{3,4,6,8,9,10}		0	333	f	(828,1314)	f	Rare Wood	f	f	f	3068	Cupdul	0	0	f		0	f	f	2
541	0	{539,542,545,547}		0	255	t	(1462,2308)	f	Wood	f	f	f	3556	Vopnaholt	0	0	f		0	f	f	1
1176	0	{1175,1177,1192}		0	345	t	(2394,2441)	f	Ivory	f	f	f	4206	Hvanseyri	0	0	f		0	f	f	4
697	5	{685,698}		0	1066	f	(2776,724)	f	Coal	f	f	f	797	Hnífshólar	0	0	f		0	f	f	1
367	0	{365,366,368}		0	250	t	(1395,1096)	f	Fur	f	f	f	4531	Seyðissey	0	0	f		0	f	f	1
478	2	{165,166,420,447,479,480}		0	327	f	(1568,677)	f	Wood	f	f	f	2886	Þórsnes	0	0	f		0	f	f	1
517	0	{252,253,267,268,273,274}		0	267	f	(1071,871)	f	Tobacco	f	f	f	4180	Vestvöllur	0	0	f		0	f	f	1
974	2	{970,973,975}		0	389	t	(4077,2667)	f	Sugar	f	f	f	2983	Stukhólar	0	0	f		0	f	f	2
932	0	{931,933,942,943,944}		0	331	t	(2914,1402)	t	Wood	f	f	f	3303	Garðaganes	0	0	f		0	f	f	1
745	2	{740,742,743,746,748,749,750}		0	328	f	(3154,207)	f	Wood	f	f	f	4123	Þorlákshólmur	0	0	f		0	f	f	3
370	1	{289,369,371,372,288,289,463}		0	106	f	(1467,904)	f	Dyes	f	f	f	523	Keflasós	0	0	f		0	f	f	3
419	2	{391,393,413,414,420,434,477,516}		0	387	f	(1564,738)	t	Spices	f	f	f	3925	Kópafjörður	0	0	f		0	f	f	2
34	0	{31,32,33,35,36,46}		0	263	f	(958,1170)	t	Grain	f	f	f	4878	Seltjarhöfn	0	0	f		0	f	f	1
387	1	{360,361,362,386,444}		0	109	f	(1453,1278)	f	Ivory	f	f	f	694	Vatroca	0	0	f		0	f	f	1
484	2	{259,266,298,299,368,369}		0	381	f	(1352,992)	f	Wood	f	f	f	2834	Hînceriopol	0	0	f		0	f	f	3
432	0	{333,335,427,431}		0	260	t	(1836,589)	f	Wool	f	f	f	3208	Tereni	0	0	f		0	f	f	2
350	5	{338,339,340,342,346,349}		0	1073	f	(1899,517)	f	Precious Stones	f	f	f	647	Iana	0	0	f		0	f	f	2
466	1	{440,465}		0	132	t	(1908,1539)	f	Spices	f	f	f	774	Rîșcați	0	0	f		0	f	f	1
722	0	{672,673,674,719,721,723}		0	387	f	(3105,583)	f	Wood	f	f	f	3690	Grolupe	0	0	f		0	f	f	2
217	2	{199,200,210,213,216,218,219}		0	364	f	(1136,412)	t	Tobacco	f	f	f	3301	Lienci	0	0	f		0	f	f	2
693	5	{692,694,696,701,702}		0	1026	f	(2837,763)	t	Silver	f	f	f	723	Vipils	0	0	f		0	f	f	3
646	2	{641,642,643,645,647}		0	382	t	(2594,182)	f	Sugar	f	f	f	4335	Aluklosta	0	0	f		0	f	f	2
206	9	{205}		0	145	t	(1039,326)	f	Fish	f	f	f	236	Salactene	0	0	f		0	f	f	2
376	1	{371,372,373,375,377,378,453,454}		0	159	f	(1600,893)	f	Spices	f	f	f	506	Ziceni	0	0	f		0	f	f	2
509	0	{508,510}		0	305	t	(520,1444)	f	Sugar	f	f	f	3007	Prielsi	0	0	f		0	f	f	3
414	5	{393,394,413,419}		0	1157	f	(1606,794)	f	Salt	f	f	f	683	Sigulda	0	0	f		0	f	f	1
417	2	{292,415,416,434,474}		0	343	f	(1417,774)	t	Tea and Coffee	f	f	f	4414	Salacele	0	0	f		0	f	f	2
455	2	{454,456,457,459}		0	345	t	(1834,918)	f	Wood	f	f	f	2706	Jauncut	0	0	f		0	f	f	1
73	0	{58,70,72,74}		0	337	t	(565,949)	f	Grain	f	f	f	4501	Vigazilani	0	0	f		0	f	f	2
14	0	{13,15}		0	272	t	(610,1278)	f	Ivory	f	f	f	4904	Salaclozi	0	0	f		0	f	f	3
218	2	{216,217,219,225,226}		0	397	t	(1152,461)	f	Tin	f	f	f	2786	Piwice	0	0	f		0	f	f	3
386	1	{362,363,364,385,387,445}		0	164	f	(1458,1224)	f	Paper	f	f	f	596	Świmyśl	0	0	f		0	f	f	1
416	2	{415,417,418,434,485}		0	352	f	(1429,823)	f	Copper	f	f	f	2864	Łomkary	0	0	f		0	f	f	1
426	0	{402,403,424,425,427}		0	348	t	(1793,686)	t	Wood	f	f	f	3410	Kory	0	0	f		0	f	f	1
219	2	{199,217,218,220,221,225}		0	333	f	(1186,403)	t	Livestock	f	f	f	3627	Śląnin	0	0	f		0	f	f	3
49	0	{27,47,48,50,51,52,53}		0	283	f	(835,1100)	t	Wood	f	f	f	3987	Jurlava	0	0	f		0	f	f	2
205	9	{203,204,206}		0	160	t	(1053,308)	f	Precious Goods	f	f	f	282	Bauslava	0	0	f		0	f	f	1
379	1	{380,381,382}		0	133	f	(1629,1075)	f	Glass	f	f	f	614	Sabidava	0	0	f		0	f	f	1
503	5	{487,488,502,506}		0	1042	t	(1264,1291)	f	Salt	f	f	f	665	Strenza	0	0	f		0	f	f	4
401	5	{400,402,403,462}		0	1264	f	(1782,745)	f	Coal	f	f	f	736	Ligatnas	0	0	f		0	f	f	2
597	0	{535,594,595,596,598,599}		0	321	f	(1080,2268)	t	Wood	f	f	f	4845	Aknibe	0	0	f		0	f	f	2
720	0	{719,721}		0	276	t	(3204,650)	f	Spices	f	f	f	3376	Alodava	0	0	f		0	f	f	1
378	1	{371,376,377,382,383}		0	103	f	(1546,997)	f	Paper	f	f	f	511	Kargava	0	0	f		0	f	f	3
406	2	{405,407,421,422,425}		0	321	f	(1674,720)	t	Wine	f	f	f	3803	Valdone	0	0	f		0	f	f	2
389	5	{370,372,388,390,485}		0	1243	f	(1521,871)	f	Coal	f	f	f	833	Limnda	0	0	f		0	f	f	4
465	1	{439,440,466}		0	146	t	(2106,1503)	f	Precious Goods	f	f	f	646	Varakgriva	0	0	f		0	f	f	2
90	2	{87,88,89,91}		0	398	t	(347,844)	f	Tobacco	f	f	f	3465	Sabigums	0	0	f		0	f	f	2
504	5	{500,505,506}		0	1112	f	(1222,1298)	f	Gold	f	f	f	899	Chezno	0	0	f		0	f	f	1
422	2	{309,311,406,421,423,425}		0	348	f	(1685,695)	t	Tobacco	f	f	f	2702	Chenowo	0	0	f		0	f	f	1
656	2	{654,655,657,658}		0	339	t	(2749,117)	f	Livestock	f	f	f	3770	Piebunalski	0	0	f		0	f	f	4
683	2	{681,682,684,716,717}		0	343	f	(2586,593)	f	Rare Wood	f	f	f	3117	Płowiec	0	0	f		0	f	f	3
161	0	{159,160,162,163,164,173,174}		0	309	f	(1478,569)	t	Fruits	f	f	f	3623	Soworzno	0	0	f		0	f	f	1
273	2	{268,269,272,274,287,289}		0	321	f	(992,844)	f	Tobacco	f	f	f	3842	Mažeikda	0	0	f		0	f	f	4
535	0	{534,536,596,597,598}		0	291	t	(1046,2169)	f	Precious Goods	f	f	f	3266	Priegara	0	0	f		0	f	f	1
508	0	{507,509}		0	270	t	(643,1444)	f	Rare Wood	f	f	f	4952	Daugbrade	0	0	f		0	f	f	3
7	0	{4,6}		0	274	t	(938,1377)	f	Wood	f	f	f	4393	Druskiai	0	0	f		0	f	f	2
857	9	{855,856,858,859,862}		0	148	t	(3663,162)	f	Fur	f	f	f	248	Marijventis	0	0	f		0	f	f	4
314	2	{302,304,305,312,313,315}		0	396	f	(1667,457)	f	Wine	f	f	f	4003	Grigtos	0	0	f		0	f	f	3
397	5	{396,398,399,407,461}		0	1075	f	(1685,787)	f	Gold	f	f	f	803	Dusetme	0	0	f		0	f	f	3
684	2	{678,681,683,685,686,716,717}		0	349	f	(2653,600)	f	Tin	f	f	f	3102	Drusštas	0	0	f		0	f	f	3
1192	0	{1176,1177,1191,1193}		0	279	t	(2371,2550)	f	Livestock	f	f	f	3020	Rudišninka	0	0	f		0	f	f	2
1153	7	{1124,1125,1154,1169,1170}		0	135	t	(2828,2126)	t	Rare Wood	f	f	f	285	Priecininkai	0	0	f		0	f	f	3
871	9	{865,866,867,868,870,872,873}		0	122	f	(3910,157)	f	Glass	f	f	f	274	Utnai	0	0	f		0	f	f	2
26	0	{24,25,27,29,30}		0	390	f	(792,1145)	f	Paper	f	f	f	4906	Mažeiklute	0	0	f		0	f	f	1
1006	0	{969,1004,1005,1007,1008}		0	308	t	(3427,1526)	t	Livestock	f	f	f	3353	Căliraolt	0	0	f		0	f	f	2
963	0	{955,956,963,964,1091,1092}		0	386	f	(3243,1407)	f	Wool	f	f	f	3911	Jurkule	0	0	f		0	f	f	4
888	0	{887,889,895,896,897}		0	360	f	(4052,542)	f	Glass	f	f	f	4638	Šventai	0	0	f		0	f	f	1
655	2	{652,653,654,656}		0	341	t	(2711,92)	f	Grain	f	f	f	2501	Vergiai	0	0	f		0	f	f	2
820	5	{813,816,819,821,824}		0	1260	f	(3393,144)	f	Spices	f	f	f	850	Galanaia	0	0	f		0	f	f	1
382	1	{378,379,381,383,384,385}		0	110	f	(1550,1060)	f	Ivory	f	f	f	508	Dukvas	0	0	f		0	f	f	3
338	5	{337,339,342,350}		0	1019	f	(1872,526)	f	Gold	f	f	f	848	Orășa	0	0	f		0	f	f	1
127	2	{113,126,128,129}		0	345	f	(814,745)	t	Fur	f	f	f	4167	Însudud	0	0	f		0	f	f	1
241	2	{232,238,240,242,276,277,278}		0	333	f	(1159,625)	f	Wine	f	f	f	4163	Bohoi	0	0	f		0	f	f	4
729	2	{668,728,730,733,734}		0	397	t	(3040,394)	t	Livestock	f	f	f	4101	Dolhadiru	0	0	f		0	f	f	3
917	0	{899,901,902,913,916,918}		0	358	f	(3883,639)	f	Rare Wood	f	f	f	3268	Ciatina	0	0	f		0	f	f	4
173	5	{161,164,167,172,174,175}		0	1036	f	(1471,634)	f	Copper	f	f	f	628	Ovilonta	0	0	f		0	f	f	3
271	0	{137,270,272,273,286,287,288}		0	328	f	(952,864)	t	Cotton	f	f	f	3569	Ramysiejai	0	0	f		0	f	f	1
96	0	{71,95,97,102,105,107}		0	287	f	(670,846)	f	Paper	f	f	f	3033	Ignalbarkas	0	0	f		0	f	f	1
951	0	{949,950,952,953,955}		0	399	f	(3319,1303)	f	Wool	f	f	f	4969	Gargbalis	0	0	f		0	f	f	1
736	2	{734,735,737,739,741}		0	340	f	(3067,299)	f	Tea and Coffee	f	f	f	4263	Dusetkiai	0	0	f		0	f	f	3
475	2	{168,169,474,476,516}		0	320	f	(1485,729)	f	Iron	f	f	f	3642	Bebiu	0	0	f		0	f	f	1
785	2	{784,786}		0	371	t	(3136,27)	f	Fish	f	f	f	3504	Jieztavas	0	0	f		0	f	f	2
433	7	{125,126,279,280,282}		0	115	t	(952,601)	t	Glass	f	f	f	253	Kaiškuva	0	0	f		0	f	f	3
716	2	{683,684,714,715,717}		0	378	f	(2626,657)	f	Salt	f	f	f	3757	Plunjoji	0	0	f		0	f	f	1
1150	0	{1139,1147,1148,1149,1151}		0	269	f	(2565,1679)	f	Grain	f	f	f	3965	Radkruojis	0	0	f		0	f	f	3
873	2	{865,871,872,874,878}		0	388	f	(3870,250)	f	Fruits	f	f	f	2900	Armănești	0	0	f		0	f	f	2
1095	0	{960,1088,1094,1096,1101,1102}		0	367	f	(3038,1638)	f	Wool	f	f	f	3988	Grimhelle	0	0	f		0	f	f	3
274	2	{252,273,283,284,289}		0	398	f	(1028,812)	f	Paper	f	f	f	3038	Oshammer	0	0	f		0	f	f	1
436	1	{435,437,464}		0	106	t	(1840,1447)	f	Dyes	f	f	f	648	Elvik	0	0	f		0	f	f	1
1217	5	{702,712,715,1215,1216}		0	1299	f	(2734,792)	f	Raw Stone	f	f	f	707	Zlačín	0	0	f		0	f	f	2
1073	7	{1063,1072,1074,1075}		0	177	t	(3351,1766)	t	Silk	f	f	f	243	Dunajňava	0	0	f		0	f	f	2
949	0	{948,950,951,955,956}		0	286	t	(3244,1316)	f	Wool	f	f	f	3093	Svärica	0	0	f		0	f	f	4
141	7	{140,142,144,268,269,270}		0	102	f	(1021,999)	f	Paper	f	f	f	226	Stropky	0	0	f		0	f	f	2
706	0	{691,704,705,708,707}		0	275	t	(2923,956)	f	Sugar	f	f	f	3991	Asrum	0	0	f		0	f	f	3
140	7	{44,139,141,142,270}		0	156	f	(1001,1006)	f	Spices	f	f	f	253	Søgjøen	0	0	f		0	f	f	4
637	9	{634,636,638,639,640}		0	106	t	(2425,124)	f	Glass	f	f	f	291	Finnros	0	0	f		0	f	f	1
1193	2	{1191,1192,1194,1195}		0	370	t	(2356,2637)	f	Tea and Coffee	f	f	f	3486	Tromvåg	0	0	f		0	f	f	1
222	2	{183,184,185,221,223,224}		0	395	f	(1296,416)	t	Livestock	f	f	f	4450	Ålerum	0	0	f		0	f	f	2
819	5	{816,818,820,824,825}		0	1282	f	(3409,153)	f	Copper	f	f	f	601	Farsøor	0	0	f		0	f	f	2
50	0	{47,49,51,135,136,138}		0	293	f	(877,1051)	f	Tobacco	f	f	f	3408	Statjøen	0	0	f		0	f	f	3
482	0	{301,303,307,483}		0	369	f	(1595,562)	f	Wood	f	f	f	3577	Breksøra	0	0	f		0	f	f	1
330	9	{328,329,331,344,345}		0	133	t	(1876,421)	f	Fish	f	f	f	273	Harvern	0	0	f		0	f	f	4
774	2	{773,775,777,778}		0	374	t	(2959,134)	f	Tobacco	f	f	f	3549	Brønnøystrøm	0	0	f		0	f	f	1
677	2	{666,675,676,678,687,688}		0	374	f	(2862,557)	f	Fur	f	f	f	4147	Kongsden	0	0	f		0	f	f	3
982	1	{977,978,981,983,987}		0	140	f	(3913,2880)	f	Paper	f	f	f	625	Verdaljøen	0	0	f		0	f	f	1
139	7	{44,137,138,140,270}		0	152	f	(952,970)	f	Spices	f	f	f	159	Dudintár	0	0	f		0	f	f	1
672	0	{669,671,673,722,723,724}		0	357	f	(3045,569)	f	Rare Wood	f	f	f	3280	Grimhalsen	0	0	f		0	f	f	1
44	0	{41,43,44,47,138,139,140,142}		0	296	f	(985,1048)	f	Wood	f	f	f	3890	Ilajov	0	0	f		0	f	f	2
242	2	{240,241,243,251,276}		0	325	f	(1145,724)	f	Livestock	f	f	f	4141	Návičovo	0	0	f		0	f	f	4
1014	0	{998,999,1013,1015}		0	339	t	(3927,1379)	f	Paper	f	f	f	3124	Baršiná	0	0	f		0	f	f	2
451	0	{449,450,452}		0	386	t	(1750,1125)	f	Spices	f	f	f	4787	Marhovec	0	0	f		0	f	f	1
233	2	{227,228,231,232,234,237,238}		0	330	f	(1219,567)	f	Fur	f	f	f	2871	Torsholm	0	0	f		0	f	f	1
463	5	{289,370,388,485}		0	1258	f	(1483,889)	f	Copper	f	f	f	668	Oxelöhall	0	0	f		0	f	f	1
1189	2	{1186,1188,1190,1196,1197,1198}		0	349	f	(2860,2655)	f	Iron	f	f	f	3082	Landskil	0	0	f		0	f	f	1
223	2	{181,183,222,224,228,229,230}		0	341	f	(1303,461)	t	Chocolate	f	f	f	4450	Ulricellefteå	0	0	f		0	f	f	4
746	2	{738,739,740,745,747,748}		0	354	f	(3177,265)	f	Rare Wood	f	f	f	3115	Bollbro	0	0	f		0	f	f	4
352	2	{340,348,351,353,359}		0	363	f	(1924,520)	f	Iron	f	f	f	4299	Gammaltorp	0	0	f		0	f	f	2
256	2	{144,145,147,253,254,255,267}		0	359	f	(1125,965)	f	Tin	f	f	f	2849	Bollbro	0	0	f		0	f	f	4
803	2	{800,801,802,804,810}		0	385	f	(3276,142)	f	Glass	f	f	f	3114	Österstad	0	0	f		0	f	f	2
319	9	{317,318,320,325}		0	153	t	(1730,378)	f	Glass	f	f	f	183	Oxelötorp	0	0	f		0	f	f	2
945	0	{944,946,957,958,959}		0	293	t	(3060,1370)	f	Sugar	f	f	f	3513	Finburg	0	0	f		0	f	f	1
965	0	{954,964,966,1005,1092,1093}		0	388	f	(3328,1461)	f	Cotton	f	f	f	3869	Uppbo	0	0	f		0	f	f	4
473	1	{469,487,488}		0	174	t	(1298,1318)	f	Paper	f	f	f	569	Borgsås	0	0	f		0	f	f	2
54	0	{23,52,53,55,56,57,61,63}		0	356	f	(697,1012)	t	Grain	f	f	f	4500	Hønekim	0	0	f		0	f	f	3
390	5	{370,372,389,391,418,485}		0	1234	f	(1537,835)	f	Spices	f	f	f	899	Snivo	0	0	f		0	f	f	2
846	9	{842,843,844,845,847,850,851}		0	147	f	(3513,150)	f	Glass	f	f	f	226	Arenstad	0	0	f		0	f	f	2
136	7	{50,51,133,134,135,137,138}		0	135	f	(880,976)	f	Coal	f	f	f	261	Ananruch	0	0	f		0	f	f	1
840	5	{831,832,839,841}		0	1225	t	(3469,115)	f	Coal	f	f	f	888	Gamlesele	0	0	f		0	f	f	1
938	0	{934,937,939,1136,1137}		0	344	f	(2662,1453)	t	Livestock	f	f	f	4802	Djurskil	0	0	f		0	f	f	1
1117	5	{1081,1112,1116,1118}		0	1062	f	(3168,2046)	f	Raw Stone	f	f	f	619	Bollhärad	0	0	f		0	f	f	1
603	0	{528,529,602,604,617}		0	256	f	(760,2358)	t	Livestock	f	f	f	4521	Uddekoga	0	0	f		0	f	f	3
1115	5	{1112,1113,1114,1116,1120,1123,1126}		0	1278	f	(3065,2037)	f	Coal	f	f	f	855	Eskilfors	0	0	f		0	f	f	2
60	0	{55,56,59,61,67,68,69,70}		0	364	f	(686,947)	t	Wood	f	f	f	3629	Sivriyayla	0	0	f		0	f	f	3
1010	0	{1001,1002,1009,1011,1012,1034,1035}		0	258	f	(3645,1476)	f	Grain	f	f	f	4417	Badekoyunlu	0	0	f		0	f	f	3
35	0	{8,33,34,36}		0	295	t	(1024,1210)	f	Tea and Coffee	f	f	f	3251	Sivrikisla	0	0	f		0	f	f	2
807	2	{757,805,806,808,809}		0	320	t	(3353,210)	f	Tea and Coffee	f	f	f	3665	Uzhhove	0	0	f		0	f	f	1
337	5	{336,338,339}		0	1104	f	(1858,542)	f	Spices	f	f	f	703	Herist	0	0	f		0	f	f	2
1044	2	{1009,1035,1043,1045,1046,1047}		0	382	f	(3569,1634)	t	Sugar	f	f	f	3297	Ahvaft	0	0	f		0	f	f	3
812	2	{811,813,821,822}		0	361	t	(3325,99)	f	Fur	f	f	f	3523	Ahvalard	0	0	f		0	f	f	3
331	9	{330,345,347,351}		0	159	t	(1917,434)	f	Precious Goods	f	f	f	293	Behbast	0	0	f		0	f	f	1
262	5	{260,261,266,289,294}		0	1029	f	(1384,916)	f	Coal	f	f	f	797	Abayaan	0	0	f		0	f	f	3
1091	0	{961,962,963,1090,1092}		0	261	f	(3216,1497)	f	Rare Wood	f	f	f	3331	Kilaqqez	0	0	f		0	f	f	2
23	0	{22,24,25,53,54,56,57}		0	344	t	(675,1064)	f	Fish	f	f	f	3017	Nibjah	0	0	f		0	f	f	1
911	0	{904,906,908,910,912,913}		0	394	f	(3762,558)	f	Grain	f	f	f	3227	Quditha	0	0	f		0	f	f	1
1039	2	{1024,1025,1026,1038,1040,1041}		0	367	f	(3837,1767)	t	Rare Wood	f	f	f	2696	Ctesirah	0	0	f		0	f	f	1
1142	0	{1132,1133,1141,1143,1144,1147,1149}		0	369	f	(2689,1706)	t	Grain	f	f	f	3237	Balasit	0	0	f		0	f	f	3
156	0	{154,155,157,179,291}		0	364	f	(1348,664)	t	Wood	f	f	f	4964	Tall-Qubayr	0	0	f		0	f	f	1
1036	0	{1033,1034,1035,1037,1043}		0	349	f	(3740,1587)	f	Paper	f	f	f	3386	Momadi	0	0	f		0	f	f	1
3	0	{1,2,4,5,10,11}		0	283	t	(812,1332)	t	Wool	f	f	f	4193	Zakhobil	0	0	f		0	f	f	3
838	5	{837,839,842,843}		0	1160	f	(3474,159)	f	Silver	f	f	f	876	Ochadilsk	0	0	f		0	f	f	2
403	5	{401,402,425,426}		0	1276	f	(1784,715)	f	Raw Stone	f	f	f	762	Berchyn	0	0	f		0	f	f	3
913	0	{904,911,912,914,916,917,918}		0	312	f	(3807,612)	t	Wool	f	f	f	4725	Mjölsås	0	0	f		0	f	f	2
877	2	{874,875,876,878,891,892,905,906}		0	342	f	(3807,394)	f	Tobacco	f	f	f	4112	Östlänge	0	0	f		0	f	f	3
107	2	{96,97,105,106,108}		0	310	t	(715,805)	t	Iron	f	f	f	2924	Huskhamn	0	0	f		0	f	f	1
1088	7	{1087,1089,1094,1095,1102,1103}		0	128	f	(3074,1672)	t	Rare Wood	f	f	f	174	Fagerbacka	0	0	f		0	f	f	2
675	0	{673,674,676,677,688,689}		0	378	t	(2946,614)	f	Paper	f	f	f	4930	Sundbyvalla	0	0	f		0	f	f	2
898	0	{897,899,916}		0	376	t	(3935,722)	f	Tea and Coffee	f	f	f	4128	Skogby	0	0	f		0	f	f	1
966	0	{953,954,965,967,1004,1005}		0	292	f	(3380,1380)	t	Grain	f	f	f	4290	Oxelögrund	0	0	f		0	f	f	1
1149	0	{1139,1140,1141,1142,1147,1150}		0	335	f	(2613,1661)	t	Livestock	f	f	f	4090	Zbodiach	0	0	f		0	f	f	1
565	7	{562,564,566,569,570}		0	101	f	(1249,2743)	f	Spices	f	f	f	263	Polonihiv	0	0	f		0	f	f	1
696	5	{685,686,687,693,694,695}		0	1080	f	(2799,695)	f	Precious Stones	f	f	f	655	Henirad	0	0	f		0	f	f	2
1033	0	{1012,1028,1032,1031,1034,1036,1037}		0	304	f	(3852,1530)	t	Fruits	f	f	f	3906	Chervonivka	0	0	f		0	f	f	2
137	7	{133,136,138,139,270,271,288}		0	101	f	(927,927)	f	Rare Wood	f	f	f	226	Illinyk	0	0	f		0	f	f	1
254	2	{249,253,255,256}		0	317	f	(1163,931)	t	Glass	f	f	f	2545	Dalabey	0	0	f		0	f	f	1
31	0	{30,32,33,34,46,48}		0	352	f	(889,1177)	t	Wood	f	f	f	4118	Pirakapi	0	0	f		0	f	f	2
67	0	{60,61,62,66,68}		0	262	f	(754,927)	t	Cotton	f	f	f	4571	Kocame	0	0	f		0	f	f	1
18	0	{16,17,19,20,21}		0	254	f	(650,1197)	f	Wool	f	f	f	3050	Kemeca	0	0	f		0	f	f	3
86	5	{78,79,85,87,93}		0	1179	f	(405,832)	f	Precious Stones	f	f	f	858	Khorashtar	0	0	f		0	f	f	1
30	0	{26,27,29,31,32,48}		0	251	f	(848,1174)	t	Glass	f	f	f	3925	Kashavar	0	0	f		0	f	f	2
308	2	{306,307,309,421,479,480}		0	325	f	(1633,637)	f	Tobacco	f	f	f	3695	Antberge	0	0	f		0	f	f	3
691	2	{689,690,692,703,704,706,707}		0	399	f	(2898,794)	f	Wood	f	f	f	2738	Grervara	0	0	f		0	f	f	2
1139	0	{1136,1137,1138,1140,1149,1150,1151}		0	380	f	(2577,1582)	f	Precious Goods	f	f	f	3469	Vöcklabühel	0	0	f		0	f	f	1
1135	0	{940,1133,1134,1136,1140,1141}		0	284	f	(2680,1589)	t	Fruits	f	f	f	3371	Wolfstadt	0	0	f		0	f	f	1
624	1	{625}		0	159	t	(2027,1600)	f	Dyes	f	f	f	602	Khushawai	0	0	f		0	f	f	2
210	2	{200,209,211,213,217}		0	338	f	(1107,355)	f	Iron	f	f	f	3042	Domamasi	0	0	f		0	f	f	4
55	0	{54,56,59,60,61}		0	281	f	(704,997)	t	Wood	f	f	f	3257	Al-Kareya	0	0	f		0	f	f	3
1037	2	{1026,1027,1028,1033,1036,1038,1042,1043}		0	379	f	(3774,1663)	t	Grain	f	f	f	3450	Bitoraele	0	0	f		0	f	f	1
282	7	{280,281,283,284,433}		0	134	f	(983,670)	t	Paper	f	f	f	211	Sammar	0	0	f		0	f	f	3
752	2	{749,750,751,753,759,800}		0	337	f	(3231,173)	f	Tobacco	f	f	f	4256	Mutuabo	0	0	f		0	f	f	1
116	2	{110,111,115,117,118}		0	343	t	(652,650)	f	Livestock	f	f	f	3357	Purbel	0	0	f		0	f	f	2
281	7	{275,276,277,280,282,283}		0	143	f	(1062,661)	f	Silk	f	f	f	287	Marralacuala	0	0	f		0	f	f	2
868	9	{867,869,870,871}		0	125	t	(3928,108)	f	Glass	f	f	f	231	Petshte	0	0	f		0	f	f	3
641	9	{642,646}		0	147	t	(2560,175)	f	Glass	f	f	f	199	Ikhlene	0	0	f		0	f	f	1
528	0	{527,529,603,617}		0	350	t	(700,2340)	f	Glass	f	f	f	3268	Tutravo	0	0	f		0	f	f	1
423	0	{311,422,424,425,428,429}		0	361	f	(1739,661)	t	Cotton	f	f	f	3567	Mallaza	0	0	f		0	f	f	2
82	0	{80,81,83,84,100,101}		0	372	f	(495,790)	f	Sugar	f	f	f	4385	Wolmadanha	0	0	f		0	f	f	2
77	2	{76,78,93}		0	315	t	(400,954)	f	Livestock	f	f	f	3810	Okashapi	0	0	f		0	f	f	2
777	2	{774,775,776,778,779}		0	396	f	(2997,127)	f	Chocolate	f	f	f	3781	Kangwon	0	0	f		0	f	f	1
483	0	{163,164,300,481,482}		0	344	f	(1577,551)	f	Paper	f	f	f	3419	Pingrao	0	0	f		0	f	f	2
421	2	{308,309,406,407,408,420,422,479}		0	308	f	(1647,688)	f	Spices	f	f	f	3521	Okairuru	0	0	f		0	f	f	1
515	2	{513,514}		0	335	t	(488,1012)	f	Tobacco	f	f	f	4143	Tattingstein	0	0	f		0	f	f	1
175	5	{158,159,172,173,174}		0	1234	f	(1465,630)	f	Coal	f	f	f	866	Tonnéte	0	0	f		0	f	f	2
1084	5	{1076,1077,1078,1083,1085}		0	1290	f	(3231,1893)	f	Coal	f	f	f	752	Vinovium	0	0	f		0	f	f	1
727	0	{724,725,726,728,730}		0	276	f	(3114,466)	t	Grain	f	f	f	3367	Liqucadis	0	0	f		0	f	f	4
164	0	{161,163,165,167,173,481,483}		0	368	f	(1512,603)	t	Glass	f	f	f	4361	Nereicada	0	0	f		0	f	f	2
967	0	{952,953,966,968,1003,1004}		0	377	t	(3513,1336)	t	Fruits	f	f	f	4033	Yirbark	0	0	f		0	f	f	3
1043	2	{1035,1036,1037,1042,1044,1047,1048}		0	382	f	(3659,1654)	t	Paper	f	f	f	3222	Jira	0	0	f		0	f	f	4
663	0	{661,662,664,667,668}		0	352	t	(2871,403)	f	Wood	f	f	f	3812	Kyratrea	0	0	f		0	f	f	2
865	9	{864,866,871,873,874}		0	128	f	(3847,223)	f	Glass	f	f	f	238	Onchapetra	0	0	f		0	f	f	1
1062	2	{1046,1049,1051,1061,1063,1064}		0	341	f	(3492,1786)	f	Wood	f	f	f	4209	Noma	0	0	f		0	f	f	2
1152	0	{1146,1147,1148,1151}		0	321	t	(2484,1731)	f	Precious Goods	f	f	f	4397	Grimbay	0	0	f		0	f	f	1
930	0	{928,929,931}		0	268	t	(2860,1291)	t	Tea and Coffee	f	f	f	3016	Borgueu	0	0	f		0	f	f	2
689	2	{675,688,690,691,692,694}		0	377	t	(2880,731)	f	Glass	f	f	f	3203	Rouyonne	0	0	f		0	f	f	2
529	0	{527,528,530,602,603}		0	382	f	(756,2297)	t	Fruits	f	f	f	3621	Nueco	0	0	f		0	f	f	3
1034	0	{1010,1012,1033,1035,1036}		0	368	f	(3758,1519)	f	Tobacco	f	f	f	3947	Talaba	0	0	f		0	f	f	1
1035	0	{1009,1010,1034,1036,1043,1044}		0	398	f	(3670,1555)	f	Tea and Coffee	f	f	f	4961	Sarfannfik	0	0	f		0	f	f	2
431	2	{312,313,332,430,432}		0	318	f	(1762,578)	f	Fruits	f	f	f	2973	Sirapaluk	0	0	f		0	f	f	3
1174	0	{1172,1173,1175}		0	390	t	(2497,2299)	f	Paper	f	f	f	3899	Pomolikeni	0	0	f		0	f	f	2
1008	0	{1002,1006,1007,1009,1045}		0	345	t	(3546,1506)	t	Fish	f	f	f	3699	Petva	0	0	f		0	f	f	4
849	9	{847,848,850,853}		0	119	t	(3521,88)	f	Glass	f	f	f	260	Chaveil	0	0	f		0	f	f	2
647	2	{645,646,648}		0	396	t	(2657,216)	f	Wine	f	f	f	3636	Križepina	0	0	f		0	f	f	1
1053	2	{1050,1052,1054,1055,1056,1057}		0	379	f	(3666,1996)	f	Iron	f	f	f	4072	Raffirowa	0	0	f		0	f	f	2
821	5	{812,813,820,822,823,824}		0	1113	f	(3391,124)	f	Raw Stone	f	f	f	659	Mirabruševo	0	0	f		0	f	f	1
580	7	{575,576,579,581,585,586}		0	155	f	(961,2738)	t	Spices	f	f	f	227	Blokstadt	0	0	f		0	f	f	2
1147	0	{1142,1144,1145,1146,1148,1149,1150,1152}		0	351	f	(2590,1740)	f	Livestock	f	f	f	4403	Waaloord	0	0	f		0	f	f	1
659	0	{660,661}		0	360	t	(2833,301)	f	Tea and Coffee	f	f	f	4879	Kraguvac	0	0	f		0	f	f	2
749	2	{745,748,750,752,753}		0	320	f	(3217,205)	f	Salt	f	f	f	4039	Škofkem	0	0	f		0	f	f	1
59	0	{55,56,58,60,70}		0	258	f	(637,965)	f	Wood	f	f	f	3315	Dudok	0	0	f		0	f	f	1
875	2	{863,864,874,876,877}		0	301	t	(3703,340)	f	Ivory	f	f	f	4440	Vsebram	0	0	f		0	f	f	3
182	2	{177,178,180,181,183}		0	376	f	(1386,479)	t	Tea and Coffee	f	f	f	3883	Heisaari	0	0	f		0	f	f	3
895	0	{888,889,894,896,900,901,902,903}		0	269	f	(3971,580)	f	Wood	f	f	f	3441	Hokkbu	0	0	f		0	f	f	4
1077	5	{1070,1075,1076,1078,1084}		0	1165	f	(3276,1902)	f	Raw Stone	f	f	f	779	Molbak	0	0	f		0	f	f	2
839	5	{838,840,841,842,847}		0	1114	f	(3472,128)	f	Salt	f	f	f	710	Osstrøm	0	0	f		0	f	f	1
507	0	{508}		0	377	t	(706,1433)	f	Rare Wood	f	f	f	4539	Varros	0	0	f		0	f	f	3
174	5	{159,161,173,175}		0	1164	f	(1471,616)	f	Salt	f	f	f	863	Verdalhelle	0	0	f		0	f	f	4
496	1	{492,494,497,498,499,505}		0	143	t	(1147,1294)	f	Glass	f	f	f	532	Ulsteinfjord	0	0	f		0	f	f	2
17	0	{15,16,18,21}		0	303	t	(621,1188)	f	Grain	f	f	f	3225	Uzhkivka	0	0	f		0	f	f	3
240	2	{238,239,241,242,243,244}		0	396	f	(1192,706)	f	Grain	f	f	f	4061	Begegaç	0	0	f		0	f	f	3
1190	0	{1178,1179,1180,1181,1182,1186,1189,1191,1196}		0	253	f	(2761,2518)	f	Wood	f	f	f	4290	Al-Hasyoun	0	0	f		0	f	f	4
306	0	{303,304,305,307,308,309,310}		0	282	f	(1649,596)	f	Grain	f	f	f	3486	Mongrieng	0	0	f		0	f	f	1
734	2	{729,733,735,736,737}		0	346	t	(3033,344)	f	Salt	f	f	f	4496	Dammum	0	0	f		0	f	f	1
808	2	{807,809,815,816}		0	366	t	(3359,191)	f	Livestock	f	f	f	2778	Moluos	0	0	f		0	f	f	3
1013	0	{999,1012,1014,1015,1016,1032}		0	372	f	(3915,1393)	f	Spices	f	f	f	3652	Mongrom	0	0	f		0	f	f	1
1067	7	{1065,1066,1068,1069,1080}		0	153	t	(3375,2034)	f	Glass	f	f	f	170	Rômbel	0	0	f		0	f	f	1
899	0	{896,897,898,900,901,917}		0	254	f	(3951,697)	t	Fur	f	f	f	4546	Probokal	0	0	f		0	f	f	2
58	0	{56,57,59,70,73}		0	264	t	(592,965)	t	Wood	f	f	f	3225	Pekandung	0	0	f		0	f	f	3
200	9	{199,201,210,211,217,219}		0	159	f	(1143,351)	f	Glass	f	f	f	292	Palangjung	0	0	f		0	f	f	1
678	2	{665,666,677,680,684,686,687}		0	330	f	(2779,573)	f	Tea and Coffee	f	f	f	3224	Pekawang	0	0	f		0	f	f	2
852	9	{845,851,854,856}		0	142	t	(3575,162)	f	Fish	f	f	f	224	Cirebau	0	0	f		0	f	f	3
715	2	{684,685,698,712,714,716,1215,1217}		0	373	f	(2680,686)	f	Wine	f	f	f	3069	Lhoklaya	0	0	f		0	f	f	4
154	0	{152,153,155,156,246,291,292}		0	387	f	(1291,700)	t	Wool	f	f	f	3031	Paloda	0	0	f		0	f	f	4
1160	0	{1159,1161,1182,1183}		0	250	t	(3121,2446)	f	Tobacco	f	f	f	4369	Pemadiun	0	0	f		0	f	f	2
144	0	{141,142,143,145,256,267,268}		0	364	t	(1089,983)	f	Ivory	f	f	f	4500	Lukah	0	0	f		0	f	f	2
248	0	{149,150,151,153,246,247}		0	274	f	(1251,839)	f	Wood	f	f	f	4770	Samagat	0	0	f		0	f	f	3
199	9	{193,198,200,201,217,219,220}		0	109	f	(1170,326)	f	Glass	f	f	f	152	Nearey	0	0	f		0	f	f	2
449	0	{338,350}		0	307	t	(1735,1172)	t	Glass	f	f	f	4481	Bhatok	0	0	f		0	f	f	1
962	0	{956,958,961,963,1091}		0	308	f	(3198,1420)	f	Grain	f	f	f	3255	Manratok	0	0	f		0	f	f	1
103	2	{102,104,105,109,110}		0	394	f	(623,727)	f	Paper	f	f	f	4014	Banmat	0	0	f		0	f	f	4
942	0	{932,933,940,941,943,1097,1098}		0	339	f	(2848,1474)	t	Glass	f	f	f	3808	Kanochang	0	0	f		0	f	f	1
593	2	{591,592,594,599,600,601}		0	387	f	(1028,2374)	f	Salt	f	f	f	2672	Patangor	0	0	f		0	f	f	2
56	0	{54,55,57,58,59,60}		0	344	f	(664,1001)	f	Grain	f	f	f	3318	Belabatangan	0	0	f		0	f	f	2
692	2	{689,691,693,694,702,703}		0	336	f	(2846,765)	f	Wood	f	f	f	4495	Maigapu	0	0	f		0	f	f	4
424	0	{423,425,426,427,428}		0	332	f	(1771,659)	f	Grain	f	f	f	4544	Aungbwe	0	0	f		0	f	f	2
64	0	{52,63,66,134,135}		0	350	f	(828,952)	t	Wood	f	f	f	3725	Aungde	0	0	f		0	f	f	4
323	9	{320,321,324,329,333,334}		0	114	f	(1784,421)	f	Glass	f	f	f	270	Senneko	0	0	f		0	f	f	1
45	0	{37,43,44,46,47}		0	360	f	(974,1096)	t	Livestock	f	f	f	3806	Kakant	0	0	f		0	f	f	1
239	2	{236,237,238,240,244,245}		0	353	f	(1222,686)	f	Rare Wood	f	f	f	3368	Cidan	0	0	f		0	f	f	3
101	0	{82,83,100}		0	268	t	(508,729)	f	Fish	f	f	f	3410	Namhpadan	0	0	f		0	f	f	1
226	2	{218,225,227,232}		0	341	t	(1174,502)	f	Grain	f	f	f	4410	Nyaungshi	0	0	f		0	f	f	3
110	2	{103,104,111,116}		0	325	t	(614,700)	f	Tobacco	f	f	f	2923	Dumadal	0	0	f		0	f	f	4
674	0	{673,675,719,722}		0	393	t	(3051,668)	f	Fish	f	f	f	3231	Samamoc	0	0	f		0	f	f	1
551	0	{549,550,552,553,554}		0	331	f	(1282,2333)	f	Glass	f	f	f	4008	Mabalacurong	0	0	f		0	f	f	1
553	0	{551,552,554,555,595,596}		0	376	f	(1204,2311)	f	Livestock	f	f	f	3881	Taguvotas	0	0	f		0	f	f	1
687	2	{677,678,688,686,694,695,696}		0	364	f	(2788,638)	f	Paper	f	f	f	3594	Galisay	0	0	f		0	f	f	3
662	0	{659,660,661,663}		0	288	t	(2869,358)	f	Wood	f	f	f	3830	Escapalay	0	0	f		0	f	f	3
1000	0	{991,997,998,999,1001,1011}		0	317	f	(3724,1337)	f	Rare Wood	f	f	f	4323	Antipi	0	0	f		0	f	f	2
1075	5	{1070,1072,1073,1074,1076,1077}		0	1266	f	(3328,1859)	f	Salt	f	f	f	732	Baido	0	0	f		0	f	f	2
1099	0	{1096,1097,1098,1100,1130}		0	335	f	(2883,1611)	t	Livestock	f	f	f	3692	Hobulla	0	0	f		0	f	f	1
568	5	{567}		0	1195	t	(1102,2765)	f	Raw Stone	f	f	f	763	Cragool	0	0	f		0	f	f	2
1109	5	{1101,1107,1108,1110,1127}		0	1038	f	(3002,1875)	f	Iron	f	f	f	888	Goulbick	0	0	f		0	f	f	2
640	9	{637,638,639}		0	195	t	(2452,99)	f	Fur	f	f	f	297	Rowvegie	0	0	f		0	f	f	1
762	0	{0}		0	372	t	(3575,261)	f	Tobacco	f	f	f	4761	Situmri	0	0	f		0	f	f	1
346	5	{342,344,345,347,349,350}		0	1108	f	(1894,490)	f	Iron	f	f	f	747	Lekamawai	0	0	f		0	f	f	2
288	2	{132,133,137,271,286}		0	374	f	(934,871)	t	Livestock	f	f	f	3402	Lumika	0	0	f		0	f	f	1
650	9	{649,651,652}		0	129	t	(2592,74)	f	Fur	f	f	f	175	Sisowai	0	0	f		0	f	f	1
564	7	{562,563,565,566}		0	120	t	(1300,2749)	f	Ivory	f	f	f	169	Benuamaiku	0	0	f		0	f	f	4
549	0	{537,538,540,548,550,551,552}		0	364	f	(1321,2268)	f	Wool	f	f	f	4363	Tabuiki	0	0	f		0	f	f	1
333	2	{321,322,323,332,334,335,432}		0	359	f	(1780,497)	f	Wood	f	f	f	3344	Tebwatao	0	0	f		0	f	f	3
847	9	{839,841,842,846,848,849,850}		0	179	f	(3501,110)	f	Glass	f	f	f	204	Aeneamaiaki	0	0	f		0	f	f	1
1141	0	{1133,1135,1140,1142,1149}		0	260	f	(2682,1647)	t	Fur	f	f	f	3552	Faiwald	0	0	f		0	f	f	3
860	9	{859,861,864,865,866}		0	101	t	(3792,175)	f	Fur	f	f	f	182	Pararaumu	0	0	f		0	f	f	3
1028	2	{1019,1027,1031,1033,1037}		0	386	f	(3902,1627)	t	Fruits	f	f	f	3873	Makelaga	0	0	f		0	f	f	1
105	2	{97,102,103,106,107}		0	305	f	(652,776)	t	Tea and Coffee	f	f	f	3509	Manatangata	0	0	f		0	f	f	2
904	0	{892,893,902,903,905,906,911,913,918}		0	359	f	(3823,517)	t	Wood	f	f	f	4530	Savaleolo	0	0	f		0	f	f	3
1097	0	{942,943,944,960,1096,1098,1099}		0	311	f	(2932,1512)	t	Wood	f	f	f	3092	Famalava	0	0	f		0	f	f	2
850	9	{846,847,849,851,853}		0	115	f	(3528,119)	f	Fur	f	f	f	152	Guatasaga	0	0	f		0	f	f	4
1195	2	{1191,1193,1194,1196,1197,1199,1200}		0	375	f	(2511,2678)	f	Chocolate	f	f	f	3438	Ninipunga	0	0	f		0	f	f	1
311	0	{309,310,422,423,429}		0	367	f	(1699,655)	f	Wood	f	f	f	4490	Katua	0	0	f		0	f	f	3
1197	2	{1189,1195,1196,1198,1200,1201}		0	325	f	(2568,2714)	f	Livestock	f	f	f	3826	Elsons Abyss	0	0	f		0	f	f	3
1183	0	{1160,1182,1184,1185}		0	271	t	(3121,2583)	f	Cotton	f	f	f	4087	Eastrock Cliffs	0	0	f		0	f	f	3
\.


--
-- Data for Name: recruitment; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.recruitment (user_id, template, sent, sent_this_month, server_id) FROM stdin;
905858887926816768	%TEMPLATE-27753325%	4083	51	674259612580446230
235228478088151041	%TEMPLATE-25352780%	6299	380	\N
793674373646909480	%TEMPLATE-27773507%	538	16	\N
293518673417732098	%TEMPLATE-25355873%	7834	0	\N
428949783919460363	%TEMPLATE-27901110%	1333	0	\N
531430986010066957	%TEMPLATE-27659356%	1386	0	\N
845341786746519613	%TEMPLATE-27918593%	79	0	\N
675835246335229986	%TEMPLATE-27894821%	425	0	\N
552224320257130496	%TEMPLATE-27023645%	403	0	\N
637939981691912202	%TEMPLATE-27758491%	10000	0	\N
695459258866729001	%TEMPLATE-27756169%	731	0	\N
844640695868194927	%TEMPLATE-27636755%	4574	161	\N
\.


--
-- Data for Name: terrains; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.terrains (id, name, modifier, color, roll) FROM stdin;
3	River	0.05		1
2	Hills	0.05	#0b6127	1
1	Desert	0.05	#D3B000	0
4	City	0.1		2
0	Plains	0	#267F00	0
6	Landing	0.1		2
5	Mountain	0.1	#5a5b5e	2
7	Swamp	0.1	#283b1b	2
9	Arctic	0.1	#C1C1EB	1
8	Fort	0.5		3
\.


--
-- Data for Name: trade_goods; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.trade_goods (name, market_value, color) FROM stdin;
Precious Stones	60	#305496
Coal	40	#404040
Wine	40	#7030A0
Fish	10	#8497B0
Tea and Coffee	40	#B45A00
Tobacco	40	#375623
Sugar	40	#E2EFDA
Fruits	50	#CC99FF
Dyes	50	#CC00FF
Wood	20	#744D26
"Rare Wood"	50	#AA7138
"Precious Goods"	70	#993366
Spices	50	#FFCC66
Livestock	20	#C6E0B4
Grain	20	#FFD966
"Raw Stone"	20	#757171
Tin	50	#B4C6E7
Ivory	60	#DBDBDB
Glass	30	#DDEBF7
Silk	50	#BDD7EE
Wool	20	#FFFFFF
Fur	30	#663300
Salt	50	#E7E6E6
Cotton	40	#FCE4D6
Silver	80	#AEAAAA
Iron	40	#595959
Chocolate	50	#9E4F00
Paper	30	#FFF2CC
Gold	90	#FFCC00
Copper	30	#EB6C15
\.


--
-- PostgreSQL database dump complete
--


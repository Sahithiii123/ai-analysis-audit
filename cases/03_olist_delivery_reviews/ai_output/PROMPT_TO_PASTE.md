# User request

Does late delivery associate with review scores, and how do seller-level late-delivery rates vary?

## Data files

The complete dataset is five CSV files, relative to the project root:

- `data/raw/03_olist_delivery_reviews/olist_customers_dataset.csv`
- `data/raw/03_olist_delivery_reviews/olist_orders_dataset.csv`
- `data/raw/03_olist_delivery_reviews/olist_order_items_dataset.csv`
- `data/raw/03_olist_delivery_reviews/olist_order_reviews_dataset.csv`
- `data/raw/03_olist_delivery_reviews/olist_sellers_dataset.csv`

Please read the full files in your Python code; the samples below are only previews.

## Data schema

### `olist_customers_dataset.csv`

| Column | Description |
|---|---|
| `customer_id` | Customer key used to join to orders. |
| `customer_unique_id` | Unique identifier of a customer. |
| `customer_zip_code_prefix` | First five digits of the customer zip code. |
| `customer_city` | Customer city name. |
| `customer_state` | Customer state. |

### `olist_orders_dataset.csv`

| Column | Description |
|---|---|
| `order_id` | Unique order identifier. |
| `customer_id` | Key to the customers file. |
| `order_status` | Order status (for example delivered, shipped, canceled). |
| `order_purchase_timestamp` | Purchase timestamp. |
| `order_approved_at` | Payment approval timestamp. |
| `order_delivered_carrier_date` | Timestamp the order was handed to the carrier. |
| `order_delivered_customer_date` | Actual delivery date to the customer. |
| `order_estimated_delivery_date` | Estimated delivery date shown at purchase. |

### `olist_order_items_dataset.csv`

| Column | Description |
|---|---|
| `order_id` | Order identifier. |
| `order_item_id` | Sequential item number within an order. |
| `product_id` | Product identifier. |
| `seller_id` | Seller identifier. |
| `shipping_limit_date` | Seller shipping limit date for the item. |
| `price` | Item price. |
| `freight_value` | Item freight cost. |

### `olist_order_reviews_dataset.csv`

| Column | Description |
|---|---|
| `review_id` | Review identifier. |
| `order_id` | Order identifier. |
| `review_score` | Satisfaction score from 1 to 5. |
| `review_comment_title` | Optional review title. |
| `review_comment_message` | Optional review comment. |
| `review_creation_date` | Date the satisfaction survey was sent. |
| `review_answer_timestamp` | Satisfaction survey answer timestamp. |

### `olist_sellers_dataset.csv`

| Column | Description |
|---|---|
| `seller_id` | Seller identifier. |
| `seller_zip_code_prefix` | First five digits of the seller zip code. |
| `seller_city` | Seller city name. |
| `seller_state` | Seller state. |

## 20-row random samples

Each sample was drawn from the real file with pandas `sample(n=20, random_state=20261016)`.

### `olist_customers_dataset.csv`

```csv
customer_id,customer_unique_id,customer_zip_code_prefix,customer_city,customer_state
c494b7ae5216760f5c7af798c3a71361,c54a7c590d22d67b17bb1059c764685b,19065,presidente prudente,SP
468e665c6f787d6cd555482460df1b3f,dab132ef31d0f8034b098624d1545e77,5056,sao paulo,SP
8fbc83a81b0932d879c867a675080329,0fad0193123898cfc5bd4cf1e387ca97,71698,brasilia,DF
caf4f7415f1dcefc703eea9c86b42951,491957a3de1bf787fca9e9af19b1e30a,3652,sao paulo,SP
2bb90453c5b070eeacd965903f376375,1003a1d72627f1a71f255e239aaa4bfd,44790,campo formoso,BA
0b3361f7d8a0472d8977bb171d80a318,576e325a9c37a4784fba13135bd20129,31720,belo horizonte,MG
2346308634084083a80df78332c411dc,297ec5afd18366f5ba27520cc4954151,5549,sao paulo,SP
a0325e9bffee8bcf4cd6e50bb677111a,9b6aaab71723727ac6a05977b6872876,7435,aruja,SP
73de2219957260ffbaaf0ea5bcc4e208,422e3a837e4b97707cac86272dc8baa9,89275,schroeder,SC
ea3acd2d48472322455ab1b6ed05f253,b83c15aacd2ade90cfadb49b5b9f881f,4421,sao paulo,SP
7cb655c040b27d290a7b3d7ef6a19ae5,7cd701c984502ec8a013a3f1ecfb87de,19470,presidente epitacio,SP
1877701b0eda5b68e5b32ccc8aa04cef,d09b41349fabc744449ba4958094cdcd,36130,rio preto,MG
6e686969d9b330c98d2739cc5d877e75,4a6fff622461f273bb0403682367d059,82630,curitiba,PR
a26826f3a4726ce0c82e8864025c150a,0e0a8fbaf8c04aa2acb0c6f4c3d92db3,4571,sao paulo,SP
3a4562b466aea32a6aa09fe85e67d400,2b87be21b33759b689e969cb8fcb9d0b,82210,curitiba,PR
57205a3f55644a1df9ea81f81aaba2c9,5994b30cf00d1fa01b52e85a243cd175,97390,lavras do sul,RS
ff6b00a007b6c413a1106354f2588a07,6752b6a9eaae810242a2428c7b1a6699,28040,campos dos goytacazes,RJ
10fa88a7b6a80c8361f3d4d83b6d384c,7ba4e1c44f34ce244666826c869e46f8,11050,santos,SP
ed40e92a9f7a1e3c77774cf6f813f3c1,707257a882dd061dac7a3b6750bd9bc2,39868,serra dos aimores,MG
5e98d1f8f0534c460557d71961a7f10a,34dd888b565982c76c7a9ee9dc41db4e,75120,anapolis,GO
```

### `olist_orders_dataset.csv`

```csv
order_id,customer_id,order_status,order_purchase_timestamp,order_approved_at,order_delivered_carrier_date,order_delivered_customer_date,order_estimated_delivery_date
d16d1a7491ec2a06c392744f9177d1ef,26f7e20b9ebc14b0de484d49ccb2305f,delivered,2017-04-20 11:09:34,2017-04-20 11:21:45,2017-04-20 12:03:46,2017-05-04 22:46:45,2017-05-31 00:00:00
fb8c006ccc9a5c06f63dc31bb472daf6,9fc8fc3c12de47e3fa73de21a6e86f4e,delivered,2017-08-22 19:37:39,2017-08-24 14:26:14,2017-08-28 17:33:16,2017-09-06 20:14:12,2017-09-18 00:00:00
9c1a5eb0f1bff32a9846477115335d36,263ea25eaa79f6e11608a9e7d210bd67,delivered,2018-05-07 11:05:20,2018-05-07 17:29:50,2018-05-09 15:48:00,2018-05-21 17:07:01,2018-06-06 00:00:00
68b4f0f2635234fcc9cbcd65b082e5b7,a0f51bf6441cdbe1a8466b0b26a3b570,delivered,2017-11-06 19:05:59,2017-11-07 03:31:17,2017-11-17 20:35:24,2017-11-28 21:26:39,2017-12-05 00:00:00
603e8f221c6d0513efe14f9de8cf4fb6,86965bfb868464bac27c29db1419610c,delivered,2018-04-14 15:51:04,2018-04-15 15:51:21,2018-04-16 23:11:51,2018-05-07 17:53:00,2018-05-14 00:00:00
48ddd457f76f31a99e60ac8007bc8b28,97fc5244045c01b3cf813cb86e6376e3,delivered,2018-01-30 10:24:25,2018-02-04 23:31:38,2018-01-31 17:59:31,2018-02-08 14:18:48,2018-03-02 00:00:00
d75e6a846d4aa0cfed378238a9147689,4db36b898bb3a416e703634b1a2ecf18,delivered,2018-08-18 18:56:33,2018-08-21 04:50:15,2018-08-23 09:38:00,2018-08-28 14:58:51,2018-09-10 00:00:00
f1227685cb32bc990c13a7c5df91005b,c9e3c1652de60db58877a8b77775ea4c,delivered,2018-04-26 09:48:57,2018-04-27 03:31:14,2018-04-30 06:21:00,2018-05-09 06:28:27,2018-05-29 00:00:00
961a93eba7486b47946616baaf442372,635907639653dd271a9d6df5bf5da1f2,delivered,2018-06-03 19:26:15,2018-06-03 19:35:12,2018-06-04 12:07:00,2018-06-11 18:55:49,2018-07-05 00:00:00
ff92b9f4c3333e0e977c4530a2e8d9cb,19256cec9e847b0c1a2922e56fec42a4,delivered,2018-06-17 10:45:05,2018-06-17 11:01:05,2018-06-18 15:53:00,2018-06-25 18:08:31,2018-07-13 00:00:00
856602c4185777967161034778407d21,e9e5f7799a82d42f2ed1eabcbabfdd56,delivered,2018-01-25 14:10:51,2018-01-26 20:53:19,2018-01-30 18:08:44,2018-02-16 21:33:02,2018-02-21 00:00:00
81a6ac5a2e54ea1f2883d6054be7b339,c1c327a1f031715cf00adc9f69fbff73,delivered,2017-02-17 10:32:57,2017-02-18 03:15:10,2017-02-20 14:27:52,2017-03-03 07:17:51,2017-03-22 00:00:00
3f63ce07f0fd566885c47bda7ad3c3a6,eceebf26966a4aed2f20b6937520fc0f,delivered,2017-03-09 19:05:16,2017-03-09 19:05:16,2017-03-10 10:35:25,2017-03-15 12:28:35,2017-04-04 00:00:00
423557ab2406aca36516f1d1b9765ae7,94273e2b4bf5b5d2cbc3af09a36ddcca,delivered,2017-02-05 12:18:08,2017-02-05 12:30:41,2017-02-07 18:14:43,2017-02-13 10:54:13,2017-03-03 00:00:00
f94a0462cf50552772e515493550bc4e,6d57ec6cb7ed54490d99bf28d64aca94,delivered,2018-02-19 13:04:45,2018-02-19 13:26:38,2018-02-20 18:39:04,2018-02-21 20:33:26,2018-03-05 00:00:00
eaa2ff40071cc82bc20cf856cc415c38,7d4525dbfd980437633dd5dea60b8cf3,delivered,2018-01-24 07:37:18,2018-01-24 07:51:44,2018-01-24 18:42:16,2018-02-02 23:06:34,2018-02-20 00:00:00
c67c6e7178cff9848b2d6556d1670fd8,3237a9ea092013b7b44c0c8d5174006d,delivered,2018-07-22 13:32:50,2018-07-23 11:32:05,2018-07-24 15:07:00,2018-07-25 17:57:42,2018-07-31 00:00:00
e212133c649bc2cb01579ef9fff04e63,507d1024879edd1c023eaad3cc4392fc,delivered,2018-01-15 11:55:00,2018-01-15 12:34:30,2018-01-17 15:09:23,2018-01-24 21:46:43,2018-02-19 00:00:00
1dfc284468e80b96e18103668871f465,36ca42c46926ac2cf4153c58fa9610f5,delivered,2017-04-24 23:02:22,2017-04-26 09:36:47,2017-04-26 13:41:56,2017-05-12 10:03:40,2017-05-15 00:00:00
a526fe23020ad8b0d2b1081b7f769452,c4ab9534c84e6ebbc22853ff357ea2ae,delivered,2018-06-23 10:27:01,2018-06-23 10:58:46,2018-06-25 12:53:00,2018-06-28 13:16:34,2018-07-12 00:00:00
```

### `olist_order_items_dataset.csv`

```csv
order_id,order_item_id,product_id,seller_id,shipping_limit_date,price,freight_value
14c32105022b0afaa60c1cae1c516e8a,1,68c923fddf7f83316b53252eaf830724,7a67c85e85bb2ce8582c35f2203ad736,2017-03-31 18:43:05,69.99,17.23
1e80bd664bc120ddf4d789b7b9455e14,2,e4ef515e041ce5062868aacf106df8b3,ca3bd7cd9f149df75950150d010fe4a2,2017-05-25 04:02:44,98.3,42.89
9eba9434978d97be47b0b7d006004669,2,5411e9269501a870cabf632f05655131,3d871de0142ce09b7081e2b9d1733cb1,2017-11-20 23:20:23,109.0,58.04
a9726615eb24e9b1fa84fe7f8c9a5b54,1,125e5760a3ff01937be3b2a1a7f14aa6,4a3ca9315b744ce9f8e9374361493884,2018-03-05 23:10:34,48.9,16.11
99bc2347537c9bba890bf1e3939f6f4e,2,eb9b44e05684527fbfdfd0ff5cb86250,df0f42bc4c2142eacf0eaf2cffd0cfbb,2018-05-04 16:54:25,104.0,18.61
d76b1c20f53889c519b279d714ddc647,1,c4baedd846ed09b85f78a781b522f126,a1043bafd471dff536d0c462352beb48,2018-03-02 16:49:59,120.0,45.3
e7fbf44c317d9ac6b87b0330fed92f1b,1,7d187801885842645486f00fb166f378,d91fb3b7d041e83b64a00a3edfb37e4f,2017-08-28 08:45:24,14.9,25.63
2a430c80705b17c17f1e9e5b138e52d5,1,cbfe76ab27b6cb27aaafcc2199f9dab9,c3867b4666c7d76867627c2f7fb22e21,2018-02-09 11:36:09,189.9,46.92
2200d7d4069cfe22127c053c75a26c17,1,efa490145b5cc82438b6a6de691535fa,8d956fec2e4337affcb520f56fd8cbfd,2018-03-21 23:10:24,46.99,17.06
d01395763bb11d18d9482f322715b80d,1,9e1260b3b3b06ad0be8cbbd26e4ec9fc,0bebbb2cea103a4a020c95d43fd7d754,2018-08-30 13:04:17,150.9,9.22
851ca56d98d52355e12410122fe07fa6,1,bcdfe7d7d9e6f6eb14f6947b0e92537b,4e922959ae960d389249c378d1c939f5,2018-07-25 08:55:29,69.0,8.64
051d3d717e96b76b07fc9076b88d671f,1,1f541a93f4fa4b8d15c7d5ed83836484,6481e96574816ead57975da2c0f6d80d,2018-02-01 03:18:35,58.5,28.11
3ffadf14829f9c35c258e08bb1982a70,1,0eda6e310c91549299a2f97d0354f7fb,57e632711dec9ec14ca7546769483e7e,2017-07-10 04:25:15,104.0,42.76
5fc3e04af31e724bfee5ffab7d3b41db,1,32edb2bfa4cfffed1e335945b86bc872,17ca9b9e9b9ef8fdb529001b49ebb50f,2018-08-02 16:20:19,69.97,27.47
b85940effca75fa13e0c2af6b056c0c2,1,9cdea37a09cb505b1c3c5d4f50670032,1e8b33f18b4f7598d87f5cbee2282cc2,2018-05-22 20:18:48,159.9,34.66
2583425d8fd6d2a22d92c8480c1b546d,3,b532349fe46b38fbc7bb3914c1bdae07,1025f0e2d44d7041d6cf58b6550e0bfa,2018-04-26 20:30:37,35.0,17.97
3fe4dbcdb046a475dbf25463c1ca78bd,1,8ad5422c2f13436a172cbdd5f2faa00e,d91fb3b7d041e83b64a00a3edfb37e4f,2017-09-05 07:00:08,35.9,16.11
c651217322b400d1c7f2fb8230870721,2,d04e48982547095af81c231c3d581cb6,7e93a43ef30c4f03f38b393420bc753a,2018-04-26 02:31:42,219.0,16.42
443b9c04691b94da8860a4b73512f94a,1,f4cd1164757f2f82e7f949e9ba129664,520b493b57809f446cb0a233bb3e25c7,2017-10-18 18:28:22,30.0,12.69
2e84df8fa5a2f0d5eab815d6c157b1f3,1,5eedf4c1aa6ce63c49b7e0c547bf0ad9,244c2f1bff6afe1f2eaf9bfe9b2aed38,2017-10-16 12:40:21,99.0,52.7
```

### `olist_order_reviews_dataset.csv`

```csv
review_id,order_id,review_score,review_comment_title,review_comment_message,review_creation_date,review_answer_timestamp
3ee13747a36e9865d38bc72f72f83a4a,bcc7f6ccd348b4d5bf8f4f7f63d4b7ef,5,,,2018-08-25 00:00:00,2018-08-25 21:06:18
3848b75c5bfe221557d5a85708d9c906,179643231d5131dc81e54ce16437972f,1,,"Meu produto não foi entregue, sem me da nenhuma informação. Cancelaram meu pedido sem me informar de nada.Nao gostei",2017-04-09 00:00:00,2017-04-09 10:12:21
a8606f402e56be47a43eac2d5384cba1,c8899924318a9e94b6bb939c2e0413d6,1,,o produto ainda nao chegou no local ,2018-03-29 00:00:00,2018-04-04 16:41:40
0418d8e3f7c8fbb67934e11a50741b6e,c88fd0ebff880ffd57fe7f6528f8dc6d,5,,"a lannister entregou super rapido, mas o tablet qbex só funcionou 24 hs, vou ter que pedir devolução",2017-11-14 00:00:00,2017-11-16 14:30:18
0c7571f1c198dee0435fe204ea197a84,3863a19752e7afd5305895ae86ee0fe0,3,,"vcs podiam abaixar o valor do frete e colocar de vez enquando frete gratis,seu frete e muito caro!!!!
",2017-12-15 00:00:00,2017-12-18 10:42:43
b300fd1a132d9a8e4af114d860a14152,d7a2737b7058006a6fb4d5e468f1feaa,5,,,2017-12-27 00:00:00,2017-12-28 02:23:44
b49e93986a2a3f320b989427313383c0,e12fe57998130b5374d8c1a89d367c04,4,,,2018-04-20 00:00:00,2018-04-23 13:06:44
6a6275671468d945f74a45201293fdf6,f0fa751754bd0d673e3eb5563ccc9d41,4,,,2017-04-19 00:00:00,2017-04-19 22:09:21
847d3c4380be05b0584f0127a0f2488d,644a46554c6d9ad03b6b8c47553ff97b,5,,,2017-12-20 00:00:00,2017-12-20 15:49:27
a8efac2a19fab9250f263478883ce4a3,8accfc040e66d8b4eac1ce4321c40911,5,,,2018-06-09 00:00:00,2018-06-09 19:25:56
760fd763df711101b76e68567cf15dc4,4a3e33350d1fd4eace1585032a97ee06,1,,,2018-08-22 00:00:00,2018-08-22 21:48:11
393907d8e4b794865eff74489af712aa,3aefaf9d41208dba8b2c336def99b00f,5,,,2017-11-08 00:00:00,2017-11-08 19:57:57
3d942e64bdacf58915ff3fdd6cfe5d54,49cb71f6609cd6b341acb1cb3ea392b1,5,,,2017-11-01 00:00:00,2017-11-03 10:16:16
769db2600a5e4ebcd21cd9a76210e6da,dceb6ab566e0d15ffaba53ef637afa3c,5,,"Só não tinha o produto que eu queria mas recebi meu dinheiro de volta.
",2017-02-23 00:00:00,2017-02-25 09:43:47
3501d2e2fea499902cb6fb754f13146d,3f191c1edeb80678998ec0c8683cefcc,1,,"PESSIMO, PERGUNTEI VÁRIAS VEZES SOBRE A ENTREGA E NINGUÉM POSICIONA",2018-03-23 00:00:00,2018-03-23 13:36:30
7d0357be02afe16ff0622748201b9f46,4aa4c6a8e7b2646986b65117bf36e67f,3,,"Só deveria cumprir com o que está no anuncio...
Veio uma cor bem diferente do anuncio... ",2018-02-16 00:00:00,2018-02-16 16:46:57
82f38e0f025e3328cae71f00e6d553bd,7a4fa3c26b5a8846a34da9564571212c,3,,,2018-06-05 00:00:00,2018-06-07 20:15:52
d53c47f8d721515f64a767b49158c927,8057ce8ffded1481446ada68f97941d6,3,,"Cadeira pelo preço que ela custa vale a pena comprar .
Foi entregue bem antes do prazo, nota 10 para este quesito.",2017-07-20 00:00:00,2017-07-21 00:20:36
8d90950debcf7d5338b1b7c2ac5fbb77,1eebc0c973e9abb0501e146fcc74b081,5,,,2018-06-23 00:00:00,2018-06-24 12:05:04
b226f53422588402db66dbc9ed51db18,a2d2af47de3679f9a5a3d9e30c46935c,5,,,2018-07-24 00:00:00,2018-07-24 20:36:14
```

### `olist_sellers_dataset.csv`

```csv
seller_id,seller_zip_code_prefix,seller_city,seller_state
116ccb1a1604bc88e4d234a8c23f33de,9850,sao bernardo do campo,SP
897060da8b9a21f655304d50fd935913,14092,ribeirao preto,SP
8e34331b7eedd03be4e5d965c1956225,4009,sao paulo,SP
81336a0f57a33776419727a300249e90,13560,sao carlos,SP
e5a3438891c0bfdb9394643f95273d8e,13483,limeira,SP
fe1b067411b8c5066e962aa146ccee03,19020,presidente prudente,SP
5d3bb11474a06bdc23fb9e89f1164ee0,19804,assis,SP
b14db04aa7881970e83ffa9426897925,18048,sorocaba,SP
bc8c8d665ec4664d286be0d521722b19,4851,sao paulo,SP
5f5a58930c3c35f3b5af264f34fb8c85,14020,ribeirao preto,SP
91543f9849d68d023e17194926598543,89041,blumenau,SC
6fc26fe110feebd80a433e1f012a84f9,15601,fernandopolis,SP
1dfe5347016252a7884b694d4f10f5c4,14940,ibitinga,SP
ba6b4a237f92479743cf0ca06b67a9ac,23550,rio de janeiro,RJ
c4b911d06343b21dd906651f8101cb49,17560,vera cruz,SP
83645b1645cdee8953ee54c29ceed564,85875,santa terezinha de itaipu,PR
3606774ec64634822d78dc2db6d37045,9510,sao caetano do sul,SP
9ef932e837d8b7f392c0bfee9d359dc2,14940,ibitinga,SP
238fac594e170b59c6d228f5a4f4f1d9,17300,dois corregos,SP
a8739afb32aaa45e01815ca76f76f54b,9850,sao bernardo do campo,SP
```

## Requested response

Please return exactly these three sections:

### Analysis plan

### Runnable Python code

Provide one Python code block that reads the complete dataset from the paths above and can run from the project root.

### Written conclusion

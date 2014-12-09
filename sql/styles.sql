-- AVERAGE IBU
UPDATE styles LEFT JOIN (SELECT style, avg(ibu) as avg_ibu FROM beers WHERE ibu > 0 AND ibu <= 200 GROUP BY style) as tmp ON tmp.style = styles.name 
SET styles.avg_ibu = tmp.avg_ibu;

UPDATE beers LEFT JOIN styles ON styles.name = style 
SET beers.ibu = styles.avg_ibu WHERE is_avg_ibu = 1 AND styles.avg_ibu IS NOT NULL;

-- AVERAGE ABV
UPDATE styles LEFT JOIN (SELECT style, avg(abv) as avg_abv FROM beers WHERE abv > 0 AND ibu <= 20 GROUP BY style) as tmp ON tmp.style = styles.name 
SET styles.avg_abv = tmp.avg_abv;

UPDATE beers LEFT JOIN styles ON styles.name = style 
SET beers.abv = styles.avg_abv WHERE is_avg_abv = 1 AND styles.avg_abv IS NOT NULL;



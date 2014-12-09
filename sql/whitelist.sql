-- Update counts for whitelist words
UPDATE word_whitelist LEFT JOIN (SELECT word_id, sum(`count`) as cnt FROM description_words GROUP BY word_id) AS tmp
ON tmp.word_id = word_whitelist.id SET word_whitelist.count = tmp.cnt;

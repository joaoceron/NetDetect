from ...preprocessing import featurize


def test_featurize_row():
  store_categoricals = preprocess.create_store_categoricals(["proto"], ["type"])
  parse_feature = preprocess.create_parse_feature(["size", "width"], ["type"], ["proto"], ["ip", "ip2"], 'flow_id')

  headers_key = {0: "size", 1: "width", 2: "type", 3: "flow_id", 4: "ip", 5: "ip2", 6: "proto"}
  raw_first = [323, '23', 'apple', 5.0, 4, 6, "chocolate:dank:shit"]
  raw_second = [22.5, '14', 'pear', 9.0, 4, 8, "chocolate:dank"]
  records = {'categorical': {}, 'protocol': {}}
  for row in [raw_first, raw_second]:
    for i, value in enumerate(row):
      field = headers_key[i]
      records = store_categoricals(field, value, records)

  clean_first = ([323.0, 23.0, 1, 0, 1, 1, 1], 5, ['4', '6'])
  clean_second = ([22.5, 14.0, 0, 1, 1, 1, 0], 9, ['4', '8'])

  assert(clean_first == preprocess.parse_row(raw_first, headers_key, parse_feature, records))
  assert(clean_second == preprocess.parse_row(raw_second, headers_key, parse_feature, records))


def test_metadatize_row():
  pass


def test_store_categoricals():
  store_categoricals = preprocess.create_store_categoricals(["proto"], ["type"])
  headers_key = {0: "size", 1: "width", 2: "type", 3: "flow_id", 4: "ip", 5: "ip2", 6: "proto"}
  raw_first = [323, '23', 'apple', 5.0, 4, 6, "chocolate:dank:shit"]
  raw_second = [22.5, '14', 'pear', 9.0, 4, 8, "chocolate:weird:blah"]
  records = {'categorical': {}, 'protocol': {}}
  for row in [raw_first, raw_second]:
    for i, value in enumerate(row):
      field = headers_key[i]
      records = store_categoricals(field, value, records)
  assert(records == {"categorical": {"type": ["apple", "pear"]}, "protocol": {"proto": ["chocolate", "dank", "shit", "weird", "blah"]}})

def test_store_categorical_over():
  store_categoricals = preprocess.create_store_categoricals(["proto"], ["type"], 2)
  headers_key = {0: "size", 1: "width", 2: "type", 3: "flow_id", 4: "ip", 5: "ip2", 6: "proto"}
  raw_first = [323, '23', 'apple', 5.0, 4, 6, "chocolate:dank:shit"]
  raw_second = [22.5, '14', 'pear', 9.0, 4, 8, "chocolate:weird:blah"]
  raw_third = [22.5, '14', 'chocolate', 9.0, 4, 8, "chocolate:weird:shit"]
  records = {'categorical': {}, 'protocol': {}}
  for j, row in enumerate([raw_first, raw_second, raw_third]):
    for i, value in enumerate(row):
      field = headers_key[i]
      if j == 2 and field == "type":
        failed = False
        try:
          records = store_categoricals(field, value, records)
        except ValueError:
          failed = True
        assert(failed)
        continue
      records = store_categoricals(field, value, records)
  assert(records == {"categorical": {"type": ["apple", "pear", "chocolate"]}, "protocol": {"proto": ["chocolate", "dank", "shit", "weird", "blah"]}})

def test_metadatize_csv():
  pass


def test_featurize_csv():
  pass


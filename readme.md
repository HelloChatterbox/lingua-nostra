# Lingua Nostra

Lingua_Nostra is chatterbox's natural language parser, it converts natural 
language into data structures, and data structures into natural language!

The main use case of lingua_nostra is handling dates and numbers

Latest version: 0.4.3

## Supported Languages

```TODO here will be a nice table comparing the state of language support ```

## Usage

see the extensive unittests!

```python
from lingua_nostra.format import nice_duration, nice_date, nice_date_time, \
    nice_number, nice_time, pronounce_number
from lingua_nostra.parse import extract_datetime, extract_number, \
    extract_numbers, extract_duration, normalize

pronounce_number(100034000000299792458, short_scale=False) 
#"one hundred trillion, thirty four thousand billion, "
#"two hundred and ninety nine million, seven hundred and ninety "
#"two thousand, four hundred and fifty eight"


extract_numbers("1 dog, seven pigs, macdonald had a farm, "
                       "3 times 5 macarena")
# [1, 7, 3, 5]
```
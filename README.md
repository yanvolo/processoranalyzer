# processoranalyzer

## Usage
script.py <input_file_name> <output_file_name> <test_name>

"test_name" refers to the value that will be attached to every cycle. This is intended so that you can distinguish individual "test" sets when analyzing the data in a larger database. 

## Behavior

Given a debug log from Chipyard, this code will use regular expressions and stream each cycle to the script to extract the value of individual fields (flags, addresses, etc.) into a Dictionary before writing results into a CSV. 

The script outputs CSV as that is the default format of Apache Superset, which the team planned to use for analysis and storage purposes. 

## Known Issues and Possible Improvements

In addition to existing @TODOS in source code:

- Prepend arbitrary date in front of "cycle_count" or create an arbitrary "date" field so that platforms like Apache Superset can natively plot this field as a time axis. 
- Skip the CSV format and simply output a JSON format. May not work with 
- Work with the Scala interface of Chipyard. This could provide the advantage of feeding data directly into other platforms. 

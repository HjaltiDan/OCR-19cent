BIN_DATA = "/home/hjalti/Gogn/Kristinarsnid/KRISTINsnid.csv"
UNCORRECTED_TXT_ROOT_FOLDER = "/home/hjalti/Gogn/Timarit-Oyfirfarid/"
CORRECTED_XML_ROOT_FOLDER = "/home/hjalti/Gogn/Timarit-YfirfaridXML/"
OLD_WORD_FREQUENCY_LIST = "gomulord.txt"
KNOWN_ERRORS = "villugrunnur.txt"
STOP_LIST_IGNORED_WORDS = "stoppord.txt"
CORRECTIONS_FILE = "leidrettingar.txt"
MINIMUM_FREQUENCY = 1
WORD_SPLIT_REGEX = " +|, |“, |“ |“$|“.$|\"$|\"\.$|„| „|\! |\? |\. |\.$|:$|: |; "
# Regex note:
#   "|" means "[or]"
#   "\" is a special character that effectively means "the following character should be read literally, and not as
#   a code for anything else". Thus, "\." means ".", "\?" means "?", etcetera.
#   " +" (note the starting space) means "[one or more spaces in a row]"
#   "$" means "[end of line]". Thus, ":$" means "[the ":" character, but only if it's the last character in this line]"

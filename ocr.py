from Levenshtein import distance as levenshtein_distance
import os
# import sys
import glob
import re
from bs4 import BeautifulSoup as bs
from config import *

# Preparation function, should be run only when needed. Creates a token frequency list from old texts that have already been reviewed and corrected.
# Tokens will only be included in the list if they consist of at least one alphabetic character.
def collate_old_words():
    ow_dict = {}
    start_directory = CORRECTED_XML_ROOT_FOLDER
    files = (file for file in os.listdir(start_directory) if os.path.isfile(os.path.join(start_directory, file)))
    for f_name in files:
        str_fullpath = start_directory + f_name

        with open(str_fullpath, "r", encoding="utf-8") as f_xml_in:
            content = f_xml_in.readlines()
            content = "".join(content)
            bs_content = bs(content, "lxml")
            token_xml_list = bs_content.find_all("t")
            for entry in token_xml_list:
                # NOTE: This line extracts the 19th century version of the word. If we want the modernized version,
                # we should instead use extracted_token = entry.text
                extracted_token = entry["c"]
                if re.search('[a-zA-ZáÁéÉíÍóÓúÚðÐþÞæÆöÖ]', extracted_token):
                    if extracted_token in ow_dict:
                        ow_dict[extracted_token] += 1
                    else:
                        ow_dict[extracted_token] = 1

    with open(OLD_WORD_FREQUENCY_LIST, "w", encoding="utf-8") as f_oldwords_out:
        for oldword_key, oldword_value in ow_dict.items():
            out_old_str = oldword_key + "\t" + str(oldword_value) + "\n"
            f_oldwords_out.write(out_old_str)


# Loads a list of words parsed from reviewed texts. Optional filter for minimum word frequency in those texts.
def load_old_words(frequency_filter=MINIMUM_FREQUENCY):
    ow_dict = {}
    with open(OLD_WORD_FREQUENCY_LIST, "r", encoding="utf-8") as f_oldword_in:
        for oldword_line in f_oldword_in:
            oldword_line = oldword_line.strip()
            line_items = oldword_line.split("\t")
            old_word_token = str(line_items[0])
            old_word_frequency = int(line_items[1])
            if old_word_frequency >= frequency_filter:
                # ow_dict[line_items[0]] = line_items[1]
                ow_dict[old_word_token] = old_word_frequency
    return ow_dict

# Loads known errors into a dict. Key is the erroneous version of a token; value is the corrected version.
def load_known_errorlist():
    ke_dict = {}
    with open(KNOWN_ERRORS, "r", encoding="utf-8") as f_errors_in:
        for f_error_line in f_errors_in:
            line_entries = f_error_line.split("\t")
            if (line_entries[1] is not None) and (line_entries is not None):
                ke_dict[line_entries[0]] = line_entries[1].strip()
    return ke_dict


def load_bin():
    b_set = set()
    with open(BIN_DATA, "r", encoding="utf-8") as f_bin_in:
        for f_bin_line in f_bin_in:
            # Choose the "ordmynd" from each line and add it to our set.
            b_set.add(f_bin_line.split(";")[9])
    return b_set


def load_stop_set():
    ss_set = set()
    with open(STOP_LIST_IGNORED_WORDS, "r", encoding="utf-8") as f_stopwords_in:
        for stopwords_line in f_stopwords_in:
            stopwords_line = stopwords_line.strip()
            ss_set.add(stopwords_line)
            # line_entries = stopwords_line.split("\t")
    return ss_set


# Return tuple of (original word, corrected version, Levenshtein length) for shortest length.
# Tiebreakers:
#   1) With equal L lengths between BIN and 19th century words, the latter wins.
#   2) If "weights" is True, tiebreakers between two 19th century words go to the one with the higher frequency.
#   3) If "weights" is False, tiebreakers between two 19tn century words go to the earlier word found.
def shortest_lev(word, oldword_dict, bin_s, oldword_weights=True):
    current_word_oldwords = ""
    current_l_oldwords = float("inf")
    current_freq_oldwords = float("inf")
    current_word_bin = ""
    current_l_bin = float("inf")
    for oldword in oldword_dict.keys():
        l_length = levenshtein_distance(word, oldword)
        if (l_length < current_l_oldwords) or (oldword_weights and (l_length == current_l_oldwords) and (oldword_dict[oldword]>current_freq_oldwords)):
            current_l_oldwords = l_length
            current_word_oldwords = oldword
            current_freq_oldwords = oldword_dict[oldword]
    for newword in bin_s:
        l_length = levenshtein_distance(word, newword)
        if (l_length < current_l_bin):
            current_l_bin = l_length
            current_word_bin = newword
    # Final selection. This code is kept separate so that it'll be easier/cleaner to add extra selection or tiebreaker criteria here later on, if needed.
    if (current_l_bin < current_l_oldwords):
        return (word, current_word_bin, current_l_bin)
    else:
        return (word, current_word_oldwords, current_l_oldwords)


# Takes in a list of known errors. Goes through the list of uncorrected documents and tries to collect a sample_size
# number of each. Stops when either all documents have been reviewed, or a sample_size number of samples has been
# collected for every error. Writes to file whatever we found thus far.
def compile_known_error_context_list(dict_known_errors, sample_size=25, outfile="error_context.txt"):
    sample_sizes_reached = False

    # Initialize our dictionary. Keys are erroneous words, values are empty lists (that will eventually contain strings)
    list_of_erroneous_words = dict_known_errors.keys()
    dict_of_samples = dict.fromkeys(list_of_erroneous_words)
    for error_key in dict_of_samples:
        dict_of_samples[error_key] = []

    with open(outfile, "w", encoding="utf-8") as f_context_out:
        if not sample_sizes_reached:
            for filename_uncorrected in glob.iglob(UNCORRECTED_TXT_ROOT_FOLDER + '**/*.txt', recursive=True):
                with open(filename_uncorrected, "r", encoding="utf-8") as f_uncorr_in:
                    uncorr_full_contents = f_uncorr_in.read()
                    uncorr_ocr_lbcr = re.sub('\.\n', '.[LBCR]', uncorr_full_contents)
                    uncorr_ocr_lbcr = re.sub('!\n', '![LBCR]', uncorr_ocr_lbcr)
                    uncorr_ocr_lbcr = re.sub('\?\n', '?[LBCR]', uncorr_ocr_lbcr)
                    uncorr_ocr_lbcr = re.sub('-\n', '', uncorr_ocr_lbcr)
                    uncorr_ocr_lbcr = re.sub('\n', ' ', uncorr_ocr_lbcr)
                    uncorr_ocr_lbcr = re.sub('\t', ' ', uncorr_ocr_lbcr)
                    ocr_full_line_list = uncorr_ocr_lbcr.split("[LBCR]")
                    # For every line in every document: Split it into tokens. For every word in the erroneous words list,
                    # compare it against every token. If there's a match, add the line to the examples list for that word.
                    for single_line in ocr_full_line_list:
                        split_token_line = list(filter(None, re.split(WORD_SPLIT_REGEX, single_line)))
                        # We could also check this with
                        # for uncorr_word in list_of_erroneous_words:
                        for uncorr_word in dict_of_samples.keys():
                            if (uncorr_word in split_token_line):
                                # Check if there's a match and if there's space left. If there's no space, check if the dictionary's full yet.
                                if len(dict_of_samples[uncorr_word])<sample_size:
                                    # Still space for samples
                                    (dict_of_samples[uncorr_word]).append(single_line)
                                else:
                                    # No space left for this particular error. Check if we're completely full up
                                    all_values_full = True
                                    for sample_list in dict_of_samples.values():
                                        if len(sample_list)<sample_size:
                                            all_values_full = False
                                    if all_values_full:
                                        # We've filled all sample lists for each error. Stop looking. We could break out of the loop, but a bool is a little cleaner
                                        sample_sizes_reached = True

        # Done. Either we've reviewed all files, or we've hit our sample_size maximums for all errors on the list.
        # Time to write out the results. The first line contains a tab-separated pair of uncorrected and corrected word.
        # Subsequent sample_size-number lines contain the samples for that error..
        for uncorr_word, sample_list in dict_of_samples.items():
            correction_str = uncorr_word + "\t" + dict_known_errors[uncorr_word] + "\n"
            f_context_out.write(correction_str)
            for sample in sample_list:
                sample_str = sample + "\n"
                f_context_out.write(sample_str)


### MAIN STARTS ###

# Run this only once
# collate_old_words()

bin_set = load_bin()
stop_set = load_stop_set()
known_error_dict = load_known_errorlist()
old_word_dict = load_old_words()
correction_dict = {}

# Run this only if you want to collect context samples for previously confirmed errors.
# compile_known_error_context_list(known_error_dict)

starting_directory = UNCORRECTED_TXT_ROOT_FOLDER

for filename in glob.iglob(starting_directory + '**/*.txt', recursive=True):
    # For Windows systems, use this rsplit instead:
    # filename_without_directory = filename.rsplit("\\", 1)[1]
    # The following line works on Unix systems
    filename_without_directory = filename.rsplit("/", 1)[1]
    filename_split_ending = filename_without_directory.rsplit(".", 1)
    filename_corrected = str(filename_split_ending[0]) + ".corr." + str(filename_split_ending[1])

    with open(filename, "r", encoding="utf-8") as f_in, open(filename_corrected, "w", encoding="utf-8") as f_out:
        ocr_full_contents = f_in.read()
        # We need to split the file contents on newline, but only when prefaced by specific non-alphanumeric characters (".", "!", "?")
        # and not by others (",", """, etc.). This can get messy and confusing if we try to do it in one step, so we'll do it in three:
        # 1) Run a substitution to differentiate our proper matches (".", "!", ...) from the others, by replacing \n with something
        # that'll never appear in the document otherwise. "[LBCR]" (line break, carriage return) should do fine.
        # 2) Discard all line-breaking "-\n", and replace remaining "\n" with whitespace.
        # 3) Now that we've separated the instances we want to split from the ones we don't, simply split on [LBCR]. No
        # need to retain any part of the match, or patch together separate strings.
        ocr_lbcr = re.sub('\.\n', '.[LBCR]', ocr_full_contents)
        ocr_lbcr = re.sub('!\n', '![LBCR]', ocr_lbcr)
        ocr_lbcr = re.sub('\?\n', '?[LBCR]', ocr_lbcr)
        ocr_lbcr = re.sub('-\n', '', ocr_lbcr)
        ocr_lbcr = re.sub('\n', ' ', ocr_lbcr)
        ocr_lbcr = re.sub('\t', ' ', ocr_lbcr)
        ocr_line_list = ocr_lbcr.split("[LBCR]")

        for line in ocr_line_list:
            # Split the sentence into constituent tokens. Some tokens will be empty; remove those with filter().
            # NOTE: Unfortunately we can't simply split with "\W". Some of the non-alphabet tokens included in \W aren't
            # word delimiters, but rather OCR errors that we need to catch.
            # NOTE #2: If we want to hold on to the split strings themselves - for example, so that they can be substituted
            # back in afterward - consider using (wrapping) for the split regex conditions.
            split_line = list(filter(None, re.split(WORD_SPLIT_REGEX, line)))

            # For every token that contains a letter, check it against our databases of known words in both BIN and 19th century terms.
            # (Tokens containing no recognizable alphabet characters are ignored.) To get around capitalization at the start of sentences,
            # check also for a lowercase version of the token. If no match is found, try to correct the token.
            for token in split_line:
                correction = ""
                if token in stop_set:
                    correction = token
                elif token in known_error_dict:
                    correction = known_error_dict[token]
                elif not (re.search('[a-zA-ZáÁéÉíÍóÓúÚðÐþÞæÆöÖ]', token)):
                    # No letters in token; no correction.
                    # This can be amended later if we want to correct specific numbers or symbols.
                    correction = token
                elif (token in old_word_dict) or (token in bin_set):
                    correction = token
                elif (token.lower() in old_word_dict) or (token.lower() in bin_set):
                    correction = token.lower()
                else:
                    # Token isn't in our lists of known words, known common 19th century words, or known OCR errors.
                    # Check twice for shortest Levenshtein distance, once in the 19th century word list, then again in BÍN.
                    # Whichever distance is the shortest, go for that. Tiebreaks go to BÍN.
                    # Obviously, this could be reprioritized. Tiebreaks could go to 19thc. And the Levenshtein distance in
                    # one of the two lists could be made to need at least x better in order to be considered: For example, if
                    # x was 2, a token with L-dist of 5 in BÍN would have to have L-dist 3 or lower in 19thc. for the 19thc.
                    # correction to be considered (or vice versa with BÍN/19thc)
                    correction_tuple = shortest_lev(token, old_word_dict, bin_set)
                    token_tuple = (correction_tuple[0], correction_tuple[1])
                    if token_tuple in correction_dict:
                        correction_dict[token_tuple] += 1
                    else:
                        correction_dict[token_tuple] = 1
                    correction = correction_tuple[1]
                out_str = token + "\t" + correction + "\n"
                f_out.write(out_str)


with open(CORRECTIONS_FILE, "w", encoding="utf-8") as f_corr_out:
    for key, value in correction_dict.items():
        corr_str = str(key[0]) + "\t" + str(key[1]) + "\t" + str(value) + "\n"
        f_corr_out.write(corr_str)

print("Program done.")

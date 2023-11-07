# reading input files
def read_input_files():
    global strings
    inputs = []
    uid = []
    with open("input.txt", "r") as file:
        strings = file.readlines()
        for string in strings:
            line = string.strip()
            line = line.split(" ")
            inputs.append([line[0], line[1]])
            uid.append(line[2])
    return inputs, uid

# write newly retrieved tokens 
def write_tokens_to_file(file_path, access_token, refresh_token):
    global strings
    strings[0] = access_token + " " + refresh_token + '\n'
    with open(file_path, 'w') as file:
        file.writelines(strings)


# main Function
def main():
    global token_lst, uid_lst, strings
    token_lst, uid_lst = read_input_files()
    access_token = "aaaaaa"
    refresh_token = "bbbbbbb"
    write_tokens_to_file("input.txt", access_token, refresh_token)


if __name__ == "__main__":

    token_lst = []
    main()

import os
import argparse


def main(args):
    if not os.path.isfile(args.input):
        raise ValueError(f'"{args.input}" is not a file or does not exist')

    script_lines = []

    with open(args.input, "r") as f:
        script_lines = f.readlines()

    variables_assignment_block = script_lines[0].strip("\n")

    assignment_statements = variables_assignment_block.split("&&")
    assignment_statements = map(
        lambda entry: entry.removeprefix("set "), assignment_statements
    )
    assignment_statements = list(
        map(lambda entry: entry.split("="), assignment_statements)
    )

    script_body = "".join(script_lines[1:])

    for variable, value in assignment_statements:
        script_body = script_body.replace(f"%{variable}%", value)

    print(script_body)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Deobfuscates strela .bat payload")
    parser.add_argument(
        metavar="<path to .bat>", dest="input", help="Specify the input .bat file"
    )

    args = parser.parse_args()
    main(args)

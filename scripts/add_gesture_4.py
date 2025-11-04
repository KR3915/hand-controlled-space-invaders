
import csv

def mirror_gesture(input_file, output_file):
    with open(input_file, 'r') as infile, open(output_file, 'a', newline='') as outfile:
        reader = csv.reader(infile)
        writer = csv.writer(outfile)

        for row in reader:
            if row and row[0] == '2':
                new_row = ['4'] + row[1:]
                for i in range(2, len(new_row), 2):
                    try:
                        new_row[i] = str(-float(new_row[i]))
                    except (ValueError, IndexError):
                        pass
                writer.writerow(new_row)

if __name__ == '__main__':
    mirror_gesture('/home/kr3915/Projects/MediaControl/data/numbers/gestures.csv', '/home/kr3915/Projects/MediaControl/data/numbers/gestures.csv')

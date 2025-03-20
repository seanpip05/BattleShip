import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


def parse_log(file_path="log.txt"):
    """ קורא את קובץ הלוג ומחזיר DataFrame עם הנתונים """
    data = []
    with open(file_path, "r") as file:
        for line in file:
            parts = line.strip().split(" - ")
            if len(parts) >= 2:
                event_type = parts[0]
                details = parts[1]
                data.append([event_type, details])

    return pd.DataFrame(data, columns=["Event", "Details"])


def analyze_shots(df):
    """ מחשב ומציג סטטיסטיקות על אחוזי הפגיעות מול ההחטאות """
    hits = df[df["Event"].str.contains("פגיעה")].shape[0]
    misses = df[df["Event"].str.contains("החטאה")].shape[0]
    total_shots = hits + misses

    if total_shots == 0:
        print("אין מספיק נתונים לניתוח")
        return

    hit_rate = (hits / total_shots) * 100
    miss_rate = (misses / total_shots) * 100

    print(f"פגיעות: {hits}, החטאות: {misses}")
    print(f"אחוזי פגיעות: {hit_rate:.2f}%, אחוזי החטאות: {miss_rate:.2f}%")

    # יצירת גרף
    labels = ["פגיעות", "החטאות"]
    values = [hit_rate, miss_rate]
    plt.bar(labels, values, color=["green", "red"])
    plt.title("אחוזי פגיעות מול החטאות")
    plt.ylabel("אחוזים")
    plt.show()


def main():
    df = parse_log()
    print("נתונים שהתקבלו:")
    print(df.head())
    analyze_shots(df)


if __name__ == "__main__":
    main()

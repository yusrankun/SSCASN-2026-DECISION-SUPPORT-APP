# 🎯 CPNS Recommendation System (Multi-Major, Jabodetabek-Oriented)

A **Streamlit-based decision support system** designed to help users find the most suitable CPNS (Indonesian civil servant) job positions across Indonesia.

This system leverages real SSCASN data and is **optimized for users in Jabodetabek (Jakarta, Bogor, Depok, Tangerang, Bekasi)** while still supporting nationwide exploration.

---

## 🚀 Features

* 📍 Location-based filtering (Jabodetabek & nationwide)
* 💰 Minimum salary filtering
* 🏢 Institution search
* ⚖️ Adjustable preference (salary vs competition)
* 🧠 Smart recommendation scoring system
* 📊 Interactive dashboard
* 📥 Export results to CSV

---

## 🧠 Scoring Method

The recommendation score is calculated using a **weighted normalized formula**:

score = (normalized_salary × weight_salary) + (inverse_competition × weight_competition)

Where:

* normalized_salary = avg_salary / max(avg_salary)
* inverse_competition = 1 / (competition_ratio + 1)

This approach ensures:

* Balanced decision-making
* No division-by-zero errors
* Flexible user preferences

---

## 📂 Project Structure

project/
│
├── app.py
├── data/
│   ├── slta.csv
│   ├── sistem_informasi.csv
│   ├── teknik_informatika.csv
│   ├── teknik_elektro.csv
│   ├── ilmu_komunikasi.csv
│   └── akuntansi.csv
├── requirements.txt
└── README.md

---

## ▶️ Installation & Run

### 1. Clone repository

git clone https://github.com/username/cpns-recommendation-system.git
cd cpns-recommendation-system

### 2. Install dependencies

pip install -r requirements.txt

### 3. Run the app

streamlit run app.py

---

## 📊 Dataset

* Source: SSCASN (BKN) API
* Coverage:

  * High school (SLTA)
  * Multiple university majors
* Total records: **30,000+ CPNS job positions**

### Includes:

* Institution
* Job title
* Location
* Salary (min & max)
* Number of positions
* Number of applicants

---

## 🎯 Design Perspective

This system is built as a **decision support tool**:

* Works **nationwide**
* Includes built-in filtering strategies optimized for **Jabodetabek users**
* Helps users balance **salary vs acceptance probability**

---

## 🏆 Use Cases

* CPNS applicants seeking data-driven decisions
* Fresh graduates targeting Jabodetabek or nearby regions
* Portfolio project for data science & decision systems

---

## 🧠 Future Improvements

* 📊 Advanced EDA dashboard
* 🌍 Map-based visualization
* 🤖 Machine learning recommendation model
* 📈 Cross-major comparison
* 🎯 Jabodetabek-only mode

---

## 👨‍💻 Author

Created by: **Zekri Fitra Ramadhan**

---

## ⭐ Notes

This project uses publicly available SSCASN data for educational purposes and is not affiliated with the Indonesian government.

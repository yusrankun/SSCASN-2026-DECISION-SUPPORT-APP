# 🎯 CPNS Recommendation System (Multi-Major)

A **Streamlit-based decision support system** to help users find the most suitable CPNS (Indonesian civil servant) job positions based on:

* 💰 Salary
* 📍 Location
* 🏢 Institution
* ⚔️ Competition level

This system supports multiple education levels and majors:

* SLTA / SMA
* Information Systems
* Informatics Engineering
* Electrical Engineering
* Communication Studies

---

## 🚀 Features

* 🔎 Filter by location (province)
* 💰 Minimum salary filtering
* 🏢 Institution search
* ⚖️ Adjustable preference (salary vs competition)
* 🧠 Smart recommendation scoring system
* 📊 Interactive data visualization
* 📥 Export results to CSV

---

## 🧠 Scoring Method

The recommendation score is calculated using a **weighted normalized formula**:

score = (normalized_salary × weight_salary) + (inverse_competition × weight_competition)

Where:

* normalized_salary = avg_salary / max(avg_salary)
* inverse_competition = 1 / (competition_ratio + 1)

This ensures:

* Balanced evaluation
* No division errors
* User-controlled preferences

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
│   └── ilmu_komunikasi.csv
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
* Covers multiple majors and education levels
* Total records: 20,000+ CPNS job openings

### Data includes:

* Institution
* Job position
* Location
* Salary (min & max)
* Number of positions
* Number of applicants

---

## 🏆 Use Cases

* Data Science portfolio
* Decision Support System (DSS)
* Public sector analytics
* Real-world recommendation system

---

## 🧠 Future Improvements

* 📊 Advanced EDA dashboard
* 🌍 Map-based visualization
* 🤖 Machine learning ranking model
* 📈 Trend analysis per institution
* 🔍 Cross-major comparison

---

## 👨‍💻 Author

Created by: **Zekri Fitra Ramadhan**

---

## ⭐ Notes

This project uses publicly available SSCASN data for educational and analytical purposes.

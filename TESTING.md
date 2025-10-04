[TESTING.md](https://github.com/user-attachments/files/22702819/TESTING.md)
# ADI Builder – Testing Checklist

This checklist helps instructors and QA staff verify that the ADI Builder app is working correctly.

---

## 1. Start the App
- Open the deployed link (e.g., `https://adi-tools.onrender.com`).
- Confirm the **ADI logo** appears in the sidebar.

---

## 2. Course Setup
- In the **sidebar**:
  1. Select **Course name** (e.g., CT4-COM).
  2. Choose **Cohort** (e.g., D1-C01).
  3. Choose your **Instructor name**.
  4. Set **Week = 1** and **Lesson = 1**.
- Check the **Outcome alignment** box: it should display the correct **KLO code** for that week.

---

## 3. Activities
1. Switch **Mode → Activities**.
2. Pick number of activities = 2.
3. Click **Generate Activities**.
   - ✅ Activities should show, e.g., *“Activity 1 (15 min): Apply — Use CT4-COM KLO1 …”*.
4. Try the **Download Activities (DOCX)** button and open the file in Word.
   - Confirm it includes **Course, Instructor, Week, Lesson, KLO** header.

---

## 4. MCQs
1. Switch **Mode → MCQs**.
2. Choose “How many MCQs?” = 5.
3. Select at least 2 Bloom verbs (e.g., *apply*, *compare*).
4. Click **Generate MCQs**.
   - ✅ Questions should not all start with “Which…” — they should use Bloom-aware templates (e.g., “Apply …”, “Evaluate …”).
   - ✅ Each question should show options A–D and an **Answer key** if selected.
5. Download the **MCQs DOCX** and check formatting in Word.

---

## 5. Revision
1. Switch **Mode → Revision**.
2. Select number of prompts = 5.
3. Click **Generate Revision**.
   - ✅ Prompts should say e.g., *“Rev 1: Recall — Summarize how CT4-COM KLO1 connects …”*.
4. Download the **Revision DOCX** and open in Word.

---

## 6. Instructor Variation
- Switch **Instructor name** in the sidebar (e.g., from *GHAMZA LABEEB KHADER* → *DANIEL JOSEPH LAMB*).
- Re-generate MCQs or Activities.
  - ✅ Content should be slightly different while still linked to the same **KLO**.

---

## 7. Override Test
- Tick **Override KLO for this lesson** in the sidebar.
- Select a different KLO than the auto-linked one.
- Regenerate Activities/MCQs/Revision.
  - ✅ New content should reference the manually chosen KLO.

---

## 8. Print Summary
- Switch **Mode → Print Summary**.
- Confirm it shows the **course, cohort, instructor, week, lesson, KLO** and the **latest generated outputs** (Activities/MCQs/Revision).

---

## 📝 Pass Criteria
- Outputs align to **correct KLO** each week.
- MCQs use **varied templates** (not all “Which”).
- **Activities and Revision** look professional, tied to course/KLO.
- **DOCX downloads** open cleanly in Word.
- **Different instructors** produce different sets.
- **Override** works when classes fall behind.

---

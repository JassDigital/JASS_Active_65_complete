import sys, os, sqlite3, csv, subprocess
from datetime import date
from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtWidgets import *

APP="JASS Active 65+"
ROOT=Path(__file__).resolve().parent
DATA=ROOT/"data"; DATA.mkdir(exist_ok=True)
DB=DATA/"jass_active65.sqlite3"

SEED_PROFILE={"age":"65","height_cm":"182.9","weight_kg":"75","activity":"Moderately active","goal":"Build and preserve muscle","diet":"Vegetarian including eggs and dairy","limitations":"None reported","sleep_hours":"6–7","notes":"One 35 g scoop Leanfit whey concentrate daily; label states 24 g protein."}
SEED_LABS=[
("Renal panel","Urea",25.88,"mg/dL","17–43","2025-02-21","Within supplied range"),
("Renal panel","BUN",12.09,"mg/dL","7–18","2025-02-21","Within supplied range"),
("Renal panel","Creatinine",0.91,"mg/dL","0.60–1.40","2025-02-21","eGFR not reported"),
("Renal panel","Uric acid",5.61,"mg/dL","3.5–7.2","2025-02-21","Within supplied range"),
("Renal panel","Potassium",4.01,"mmol/L","3.5–5.5","2025-02-21","Within supplied range"),
("Renal panel","Sodium",142.5,"mmol/L","136–149","2025-02-21","Within supplied range"),
("Lipid profile","Total cholesterol",274.44,"mg/dL","Desirable <200","","Historical; date not confirmed in report image"),
("Lipid profile","Triglycerides",212.99,"mg/dL","<150 desirable","","Historical; date not confirmed in report image"),
("Lipid profile","HDL cholesterol",44.96,"mg/dL",">40","","Historical; date not confirmed in report image"),
("Lipid profile","LDL cholesterol",186.88,"mg/dL","Individual targets vary","","High historical result; clinician review advised"),
("Lipid profile","VLDL",42.60,"mg/dL","6–38","","Above supplied range"),
("Lipid profile","Cholesterol/HDL ratio",6.10,"ratio","0–4","","Above supplied range"),
("Lipid profile","LDL/HDL ratio",4.16,"ratio","1–3","","Above supplied range"),
("Glucose","Fasting glucose",99.12,"mg/dL","70–100","2025-02-21","Historical result"),
("Glucose","HbA1c",5.5,"%","<5.7","2025-02-21","Historical result"),
("Glucose","Estimated average glucose",111.15,"mg/dL","","2025-02-21","Lab-reported estimate"),
("Vitamin","25-OH Vitamin D",46.2,"ng/mL","30–100","2025-02-21","Historical result"),
("Vitamin","Vitamin B12",550,"pg/mL","187–883","2025-02-21","Historical result"),
("Thyroid","T3",1.01,"ng/mL","0.35–1.93","2025-02-21","Historical result"),
("Thyroid","T4",5.80,"µg/dL","4.87–11.72","2025-02-21","Historical result"),
("Thyroid","TSH",1.72,"µIU/mL","0.35–4.94","2025-02-21","Historical result"),
("Mineral","Phosphorus",3.09,"mg/dL","2.1–5.6","2025-02-21","Historical result"),
("Liver panel","Total protein",7.37,"g/dL","6.6–8.3","","Date not confirmed in image"),
("Liver panel","Albumin",4.55,"g/dL","3.2–4.6","","Date not confirmed in image"),
("Liver panel","Globulin",2.82,"g/dL","1.8–3.6","","Date not confirmed in image"),
("Liver panel","A/G ratio",1.61,"ratio","1.2–2.2","","Date not confirmed in image"),
("Liver panel","Total bilirubin",0.92,"mg/dL","0–1.20","","Date not confirmed in image"),
("Liver panel","Direct bilirubin",0.12,"mg/dL","<0.30","","Date not confirmed in image"),
("Liver panel","Indirect bilirubin",0.80,"mg/dL","0–1.0","","Date not confirmed in image"),
("Liver panel","AST/SGOT",20.42,"U/L","<50","","Date not confirmed in image"),
("Liver panel","ALT/SGPT",33.80,"U/L","<50","","Date not confirmed in image"),
("Liver panel","ALP",81.79,"U/L","30–120","","Date not confirmed in image"),
("CBC","Haemoglobin",14.2,"g/dL","12–16","","Date not confirmed in image"),
("CBC","RBC",5.60,"million/cu.mm","4.7–6.0","","Date not confirmed in image"),
("CBC","PCV",45.67,"%","42–52","","Date not confirmed in image"),
("CBC","MCV",82.75,"fL","80–100","","Date not confirmed in image"),
("CBC","MCH",25.10,"pg","27–31","","Low in supplied report"),
("CBC","MCHC",30.46,"g/dL","32–36","","Low in supplied report"),
("CBC","RDW",11.6,"%","11.5–14","","Date not confirmed in image"),
("CBC","WBC",6.3,"10^9/L","4–11","","Date not confirmed in image"),
("CBC","Platelets",156,"10^9/L","140–450","","Lower end of supplied range"),
("PSA","PSA",1.81,"ng/mL","0–4","","Date not confirmed in image"),
("Urine","Specific gravity",1.015,"","1.005–1.030","","Date not confirmed in image"),
("Urine","pH",7.0,"","4.5–7.0","","Date not confirmed in image"),
("Urine","Urine protein",0,"","Absent","","Absent"),
("Urine","Urine glucose",0,"","Absent","","Absent"),
("Urine","RBC",0,"/hpf","0–4","","Absent"),
("Urine","Pus cells",0.5,"/hpf","0–9","","0–1/hpf reported")
]

def dbopen():
    c=sqlite3.connect(DB)
    c.executescript("""
    CREATE TABLE IF NOT EXISTS profile(k TEXT PRIMARY KEY,v TEXT);
    CREATE TABLE IF NOT EXISTS labs(id INTEGER PRIMARY KEY,category TEXT,test TEXT,value REAL,unit TEXT,reference TEXT,test_date TEXT,notes TEXT);
    CREATE TABLE IF NOT EXISTS fitness(id INTEGER PRIMARY KEY,entry_date TEXT,activity TEXT,duration INTEGER,sets INTEGER,reps INTEGER,notes TEXT);
    CREATE TABLE IF NOT EXISTS nutrition(id INTEGER PRIMARY KEY,entry_date TEXT,food TEXT,protein REAL,calories REAL,notes TEXT);
    CREATE TABLE IF NOT EXISTS supplements(id INTEGER PRIMARY KEY,name TEXT,dose TEXT,frequency TEXT,status TEXT,notes TEXT);
    CREATE TABLE IF NOT EXISTS vitality(id INTEGER PRIMARY KEY,entry_date TEXT,libido INTEGER,firmness INTEGER,maintenance TEXT,morning INTEGER,sleep REAL,notes TEXT);
    CREATE TABLE IF NOT EXISTS appointments(id INTEGER PRIMARY KEY,entry_date TEXT,subject TEXT,notes TEXT,done INTEGER DEFAULT 0);
    """)
    if not c.execute("SELECT COUNT(*) FROM profile").fetchone()[0]:
        c.executemany("INSERT INTO profile VALUES(?,?)",SEED_PROFILE.items())
    if not c.execute("SELECT COUNT(*) FROM labs").fetchone()[0]:
        c.executemany("INSERT INTO labs(category,test,value,unit,reference,test_date,notes) VALUES(?,?,?,?,?,?,?)",SEED_LABS)
    if not c.execute("SELECT COUNT(*) FROM supplements").fetchone()[0]:
        c.executemany("INSERT INTO supplements(name,dose,frequency,status,notes) VALUES(?,?,?,?,?)",[
        ("Leanfit whey concentrate","35 g; 24 g protein","Daily","Active","Count toward daily protein."),
        ("Vitamin D3","2,500 IU","Daily","Active","Historical 25-OH D 46.2 ng/mL (2025-02-21); review current level and dose with clinician."),
        ("Webber Naturals Omega-3","900 mg; 600 mg EPA + 300 mg DHA","Daily","Active","Review with clinician; not a substitute for lipid treatment."),
        ("Webber Naturals B50","As per label","Occasionally","Occasional","Check B6 content if use becomes frequent.")])
    c.commit(); return c

class App(QMainWindow):
 def __init__(self):
    super().__init__(); self.c=dbopen(); self.setWindowTitle(APP+" | Personal Health & Fitness"); self.resize(1360,850)
    self.setStyleSheet("""
    QMainWindow{background:#f2f5f9} QWidget{font-family:Segoe UI,Arial;color:#243247}
    QFrame#side{background:#17283e} QFrame#side QLabel{color:white}
    QPushButton{padding:9px 12px;border:0;border-radius:6px;background:#e6edf5;text-align:left}
    QPushButton:hover{background:#d2e2f3} QPushButton#primary{background:#1769aa;color:white;font-weight:bold}
    QLineEdit,QTextEdit,QComboBox,QSpinBox,QDoubleSpinBox,QDateEdit{padding:6px;border:1px solid #cbd5e1;border-radius:5px;background:white}
    QTableWidget{background:white;gridline-color:#e5eaf0} QHeaderView::section{background:#e5edf6;padding:7px;border:0}
    QGroupBox{background:white;border:1px solid #dce4ed;border-radius:8px;margin-top:9px;padding:10px;font-weight:bold}
    """)
    root=QWidget(); self.setCentralWidget(root); h=QHBoxLayout(root); h.setContentsMargins(0,0,0,0)
    side=QFrame(); side.setObjectName("side"); side.setFixedWidth(225); sv=QVBoxLayout(side); sv.setContentsMargins(14,20,14,14)
    sv.addWidget(QLabel("JASS ACTIVE 65+")); sv.addWidget(QLabel("Health • Fitness • Vitality")); sv.addSpacing(18)
    self.stack=QStackedWidget(); self.nav=[]
    pages=[("Dashboard",self.dashboard),("My Profile",self.profile),("Fitness & Strength",self.fitness),("Nutrition",self.nutrition),("Supplements",self.supplements),("Men's Vitality",self.vitality),("Lab Records",self.labs),("Health Trends",self.trends),("Appointments",self.appointments),("Reports & Backup",self.reports)]
    for name,fn in pages:
        b=QPushButton(name); b.clicked.connect(lambda _,n=name,f=fn:self.navigate(n,f)); sv.addWidget(b); self.nav.append(b)
    sv.addStretch(); sv.addWidget(QLabel("Offline • Local SQLite")); h.addWidget(side); h.addWidget(self.stack,1); self.navigate("Dashboard",self.dashboard)
 def page(self,title,sub=""):
    w=QWidget(); v=QVBoxLayout(w); v.setContentsMargins(25,22,25,20); v.addWidget(QLabel(title))
    w.findChild(QLabel).setStyleSheet("font-size:22pt;font-weight:700;color:#173f66")
    if sub:
        l=QLabel(sub); l.setWordWrap(True); l.setStyleSheet("color:#64748b"); v.addWidget(l)
    return w,v
 def navigate(self,n,fn):
    for b in self.nav: b.setStyleSheet("background:#294563;color:white" if b.text()==n else "")
    w=fn(); self.stack.addWidget(w); self.stack.setCurrentWidget(w)
    while self.stack.count()>1:
        old=self.stack.widget(0)
        if old is not w:self.stack.removeWidget(old);old.deleteLater()
        else:break
 def card(self,t,val,detail):
    f=QFrame(); f.setStyleSheet("QFrame{background:white;border:1px solid #dce4ed;border-radius:9px;padding:12px}")
    x=QVBoxLayout(f); a=QLabel(t);a.setStyleSheet("color:#64748b;font-weight:bold");b=QLabel(val);b.setStyleSheet("font-size:21pt;font-weight:bold;color:#1769aa");d=QLabel(detail);d.setWordWrap(True);d.setStyleSheet("color:#64748b;font-size:9pt");x.addWidget(a);x.addWidget(b);x.addWidget(d);return f
 def dashboard(self):
    w,v=self.page("Your health, strength and vitality","Personal overview. Historical laboratory values are not current measurements.")
    p=dict(self.c.execute("SELECT k,v FROM profile"));g=QGridLayout()
    for i,args in enumerate([("AGE",p.get("age","65")+" years","Profile"),("WEIGHT",p.get("weight_kg","75")+" kg","Profile"),("HEIGHT",p.get("height_cm","182.9")+" cm","Profile"),("BMI","22.4","Calculated from supplied profile")]):g.addWidget(self.card(*args),0,i)
    v.addLayout(g)
    box=QGroupBox("Important follow-up");x=QVBoxLayout(box)
    for s in ["Historical LDL 186.88 mg/dL and triglycerides 212.99 mg/dL: repeat lipid profile and arrange clinician review soon.","Historical CBC showed low MCH/MCHC: discuss ferritin and iron studies before taking iron.","Historical kidney panel did not include eGFR or urine albumin-to-creatinine ratio.","Gradual erection-maintenance difficulty: discuss cardiovascular risk and sexual-health assessment with your clinician."]:
        x.addWidget(QLabel("• "+s))
    v.addWidget(box)
    box2=QGroupBox("Programme targets");x2=QGridLayout(box2)
    for i,(a,b) in enumerate([("Strength","3 sessions weekly"),("Walking","Build toward 150 min weekly"),("Protein","Provisional 90–95 g/day; review kidney status"),("Sleep","Aim for 7–9 hours"),("Balance","Several short sessions weekly"),("Weight","Maintain healthy weight")]):
        x2.addWidget(QLabel(a),i//2,(i%2)*2);x2.addWidget(QLabel(b),i//2,(i%2)*2+1)
    v.addWidget(box2);v.addStretch();return w
 def profile(self):
    w,v=self.page("My Profile","Edit your baseline; historical laboratory records remain unchanged.")
    form=QFormLayout(); fields={}
    labels={"age":"Age","height_cm":"Height (cm)","weight_kg":"Weight (kg)","activity":"Activity","goal":"Goal","diet":"Diet","limitations":"Limitations","sleep_hours":"Typical sleep","notes":"Notes"}
    for k,l in labels.items():
        e=QLineEdit(self.c.execute("SELECT v FROM profile WHERE k=?",(k,)).fetchone()[0]);fields[k]=e;form.addRow(l,e)
    v.addLayout(form);b=QPushButton("Save profile");b.setObjectName("primary")
    def save():
        self.c.executemany("INSERT INTO profile(k,v) VALUES(?,?) ON CONFLICT(k) DO UPDATE SET v=excluded.v",[(k,e.text()) for k,e in fields.items()]);self.c.commit();QMessageBox.information(self,"Saved","Profile updated.")
    b.clicked.connect(save);v.addWidget(b);v.addStretch();return w
 def generic_table(self,title,sub,query,headers,form_builder=None):
    w,v=self.page(title,sub);bar=QHBoxLayout();refresh=QPushButton("Refresh");export=QPushButton("Export CSV");bar.addWidget(refresh);bar.addWidget(export);bar.addStretch();v.addLayout(bar)
    t=QTableWidget();t.setColumnCount(len(headers));t.setHorizontalHeaderLabels(headers);t.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents);t.horizontalHeader().setStretchLastSection(True);v.addWidget(t,1)
    def load():
        rows=self.c.execute(query).fetchall();t.setRowCount(len(rows))
        for r,row in enumerate(rows):
            for j,val in enumerate(row):t.setItem(r,j,QTableWidgetItem("" if val is None else str(val)))
    refresh.clicked.connect(load);load()
    def exp():
        path,_=QFileDialog.getSaveFileName(self,"Export CSV",title.lower().replace(" ","_")+".csv","CSV (*.csv)")
        if path:
            with open(path,"w",newline="",encoding="utf-8-sig") as f:
                z=csv.writer(f);z.writerow(headers);z.writerows(self.c.execute(query).fetchall())
            QMessageBox.information(self,"Exported",path)
    export.clicked.connect(exp)
    if form_builder:form_builder(v,load)
    return w
 def fitness(self):
    def form(v,load):
        box=QGroupBox("Log exercise");f=QFormLayout(box);a=QComboBox();a.addItems(["Walking","Chair squats","Push-ups","Pull-ups","Resistance-band rows","Calf raises","Balance","Mobility","Other"])
        d=QSpinBox();d.setRange(0,600);d.setSuffix(" min");s=QSpinBox();s.setRange(0,100);r=QSpinBox();r.setRange(0,500);n=QLineEdit()
        for l,x in [("Activity",a),("Duration",d),("Sets",s),("Reps",r),("Notes",n)]:f.addRow(l,x)
        b=QPushButton("Save session");b.setObjectName("primary")
        def save():
            self.c.execute("INSERT INTO fitness(entry_date,activity,duration,sets,reps,notes) VALUES(?,?,?,?,?,?)",(date.today().isoformat(),a.currentText(),d.value(),s.value(),r.value(),n.text()));self.c.commit();load()
        b.clicked.connect(save);v.addWidget(box);v.addWidget(b)
    return self.generic_table("Fitness & Strength","Log walking, resistance training, balance and mobility.","SELECT entry_date,activity,duration,sets,reps,notes FROM fitness ORDER BY id DESC",["Date","Activity","Minutes","Sets","Reps","Notes"],form)
 def nutrition(self):
    w,v=self.page("Nutrition & Protein","Log foods and protein. A 90–95 g/day target is provisional, not a prescription; review with clinician and current kidney tests.")
    box=QGroupBox("Add food entry");f=QFormLayout(box);food=QLineEdit();p=QDoubleSpinBox();p.setRange(0,300);p.setSuffix(" g protein");cal=QDoubleSpinBox();cal.setRange(0,5000);cal.setSuffix(" kcal");notes=QLineEdit()
    for l,x in [("Food / meal",food),("Protein",p),("Calories",cal),("Notes",notes)]:f.addRow(l,x)
    b=QPushButton("Add entry");b.setObjectName("primary");v.addWidget(box);v.addWidget(b);suml=QLabel();v.addWidget(suml)
    t=QTableWidget();t.setColumnCount(5);t.setHorizontalHeaderLabels(["Date","Food","Protein g","Calories","Notes"]);t.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents);t.horizontalHeader().setStretchLastSection(True);v.addWidget(t,1)
    def load():
        rows=self.c.execute("SELECT entry_date,food,protein,calories,notes FROM nutrition ORDER BY id DESC LIMIT 250").fetchall();t.setRowCount(len(rows))
        for i,row in enumerate(rows):
            for j,val in enumerate(row):t.setItem(i,j,QTableWidgetItem(str(val if val is not None else "")))
        total=self.c.execute("SELECT COALESCE(SUM(protein),0) FROM nutrition WHERE entry_date=?",(date.today().isoformat(),)).fetchone()[0];suml.setText(f"Protein logged today: {total:.1f} g")
    def save():
        if food.text().strip():self.c.execute("INSERT INTO nutrition(entry_date,food,protein,calories,notes) VALUES(?,?,?,?,?)",(date.today().isoformat(),food.text(),p.value(),cal.value(),notes.text()));self.c.commit();food.clear();load()
    b.clicked.connect(save);load();return w
 def supplements(self):
    def form(v,load):
        box=QGroupBox("Add supplement");f=QFormLayout(box);name=QLineEdit();dose=QLineEdit();freq=QLineEdit();status=QComboBox();status.addItems(["Active","Occasional","Paused","Stopped"]);notes=QLineEdit()
        for l,x in [("Name",name),("Dose",dose),("Frequency",freq),("Status",status),("Notes",notes)]:f.addRow(l,x)
        b=QPushButton("Save");b.setObjectName("primary")
        def save():
            self.c.execute("INSERT INTO supplements(name,dose,frequency,status,notes) VALUES(?,?,?,?,?)",(name.text(),dose.text(),freq.text(),status.currentText(),notes.text()));self.c.commit();load()
        b.clicked.connect(save);v.addWidget(box);v.addWidget(b)
    return self.generic_table("Supplements","Personal register only; review doses and interactions with your clinician.","SELECT name,dose,frequency,status,notes FROM supplements ORDER BY id",["Name","Dose","Frequency","Status","Notes"],form)
 def vitality(self):
    w,v=self.page("Men's Vitality & Sexual Wellness","Private optional self-tracking. No score is a diagnosis or a measure of personal worth.")
    box=QGroupBox("Private check-in");f=QFormLayout(box);lib=QSpinBox();lib.setRange(1,5);lib.setValue(4);firm=QSpinBox();firm.setRange(1,4);firm.setValue(3);maint=QComboBox();maint.addItems(["Not recorded","Usually maintained","Sometimes loses firmness","Often loses firmness"]);mor=QSpinBox();mor.setRange(0,7);mor.setSuffix(" days/week");sleep=QDoubleSpinBox();sleep.setRange(0,16);sleep.setValue(6.5);sleep.setSuffix(" hours");notes=QLineEdit()
    for l,x in [("Libido (1–5)",lib),("Erection hardness (1–4)",firm),("Maintenance",maint),("Morning erections",mor),("Sleep",sleep),("Notes (optional)",notes)]:f.addRow(l,x)
    b=QPushButton("Save private check-in");b.setObjectName("primary");v.addWidget(box);v.addWidget(b)
    t=QTableWidget();t.setColumnCount(7);t.setHorizontalHeaderLabels(["Date","Libido","Firmness","Maintenance","Morning erections","Sleep","Notes"]);t.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents);t.horizontalHeader().setStretchLastSection(True);v.addWidget(t,1)
    def load():
        rows=self.c.execute("SELECT entry_date,libido,firmness,maintenance,morning,sleep,notes FROM vitality ORDER BY id DESC").fetchall();t.setRowCount(len(rows))
        for i,row in enumerate(rows):
            for j,val in enumerate(row):t.setItem(i,j,QTableWidgetItem(str(val if val is not None else "")))
    def save():
        self.c.execute("INSERT INTO vitality(entry_date,libido,firmness,maintenance,morning,sleep,notes) VALUES(?,?,?,?,?,?,?)",(date.today().isoformat(),lib.value(),firm.value(),maint.currentText(),mor.value(),sleep.value(),notes.text()));self.c.commit();load()
    b.clicked.connect(save);load();return w
 def labs(self):
    def form(v,load):
        box=QGroupBox("Add new lab result — historical entries are preserved");f=QFormLayout(box);cat=QLineEdit();test=QLineEdit();val=QDoubleSpinBox();val.setRange(-1000000,1000000);val.setDecimals(4);unit=QLineEdit();ref=QLineEdit();dt=QDateEdit();dt.setCalendarPopup(True);dt.setDate(date.today());notes=QLineEdit()
        for l,x in [("Category",cat),("Test",test),("Value",val),("Unit",unit),("Reference",ref),("Date",dt),("Notes",notes)]:f.addRow(l,x)
        b=QPushButton("Add result");b.setObjectName("primary")
        def save():
            if not test.text().strip():QMessageBox.warning(self,"Required","Enter test name.");return
            self.c.execute("INSERT INTO labs(category,test,value,unit,reference,test_date,notes) VALUES(?,?,?,?,?,?,?)",(cat.text(),test.text(),val.value(),unit.text(),ref.text(),dt.date().toString("yyyy-MM-dd"),notes.text()));self.c.commit();load()
        b.clicked.connect(save);v.addWidget(box);v.addWidget(b)
    return self.generic_table("Laboratory Records","Imported historical results are retained. Blank dates mean the date was not visible in the supplied report.","SELECT test_date,category,test,value,unit,reference,notes FROM labs ORDER BY COALESCE(test_date,'1900-01-01') DESC,category,test",["Date","Category","Test","Value","Unit","Reference","Notes"],form)
 def trends(self):
    w,v=self.page("Health Trends","Compare like-for-like results with matching units. Historical results are not current status.")
    t=QTableWidget();t.setColumnCount(6);t.setHorizontalHeaderLabels(["Test","Date","Value","Unit","Reference","Notes"]);t.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents);t.horizontalHeader().setStretchLastSection(True)
    rows=self.c.execute("SELECT test,test_date,value,unit,reference,notes FROM labs ORDER BY test,test_date").fetchall();t.setRowCount(len(rows))
    for i,row in enumerate(rows):
        for j,val in enumerate(row):t.setItem(i,j,QTableWidgetItem(str(val if val is not None else "")))
    v.addWidget(t,1);v.addWidget(QLabel("Discuss updated lipid profile, blood pressure, HbA1c, creatinine/eGFR and urine ACR with your clinician. Consider ApoB and one-time Lp(a) where appropriate. For previous low MCH/MCHC, discuss ferritin and iron studies."))
    return w
 def appointments(self):
    def form(v,load):
        box=QGroupBox("Add follow-up");f=QFormLayout(box);dt=QDateEdit();dt.setCalendarPopup(True);dt.setDate(date.today());sub=QLineEdit();note=QLineEdit()
        for l,x in [("Date",dt),("Subject",sub),("Notes",note)]:f.addRow(l,x)
        b=QPushButton("Save reminder");b.setObjectName("primary")
        def save():
            self.c.execute("INSERT INTO appointments(entry_date,subject,notes) VALUES(?,?,?)",(dt.date().toString("yyyy-MM-dd"),sub.text(),note.text()));self.c.commit();load()
        b.clicked.connect(save);v.addWidget(box);v.addWidget(b)
    return self.generic_table("Appointments & Follow-up","Record clinician reviews, tests and fitness assessments.","SELECT entry_date,subject,notes,CASE done WHEN 1 THEN 'Done' ELSE 'Open' END FROM appointments ORDER BY entry_date",["Date","Subject","Notes","Status"],form)
 def reports(self):
    w,v=self.page("Reports & Backup","Your data stays in a local SQLite database. Protect it as sensitive personal information.")
    v.addWidget(QLabel(f"Database: {DB}"))
    b=QPushButton("Export all tables to CSV folder");b.setObjectName("primary")
    def export():
        folder=QFileDialog.getExistingDirectory(self,"Choose export folder")
        if not folder:return
        for table in ["profile","labs","fitness","nutrition","supplements","vitality","appointments"]:
            cur=self.c.execute("SELECT * FROM "+table)
            with open(os.path.join(folder,table+".csv"),"w",newline="",encoding="utf-8-sig") as f:
                z=csv.writer(f);z.writerow([d[0] for d in cur.description]);z.writerows(cur.fetchall())
        QMessageBox.information(self,"Export complete","CSV files exported.")
    b.clicked.connect(export);v.addWidget(b)
    b2=QPushButton("Create SQLite backup")
    def backup():
        path,_=QFileDialog.getSaveFileName(self,"Save backup","jass_active65_backup.sqlite3","SQLite (*.sqlite3)")
        if path:
            dest=sqlite3.connect(path);self.c.backup(dest);dest.close();QMessageBox.information(self,"Backup","Backup created.")
    b2.clicked.connect(backup);v.addWidget(b2)
    b3=QPushButton("Open data folder")
    def openfolder():
        try:
            if sys.platform.startswith("win"):os.startfile(str(DATA))
            elif sys.platform=="darwin":subprocess.Popen(["open",str(DATA)])
            else:subprocess.Popen(["xdg-open",str(DATA)])
        except Exception as e:QMessageBox.warning(self,"Open folder",str(e))
    b3.clicked.connect(openfolder);v.addWidget(b3)
    v.addWidget(QLabel("Medical safety: this is a record-keeping and planning tool, not a diagnostic or prescribing system. Discuss abnormal results with a qualified clinician. Do not start iron, testosterone, ED medication or supplements solely based on app entries."));v.addStretch();return w
 def closeEvent(self,e):self.c.close();e.accept()

if __name__=="__main__":
 app=QApplication(sys.argv);app.setStyle("Fusion");win=App();win.show();sys.exit(app.exec())


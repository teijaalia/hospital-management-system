function isAlpha(c) {
    return /^[A-Za-z]$/.test(c);
}
function isNumeric(c) {
    return /^[0-9]$/.test(c);
}

function CleanString(str){
  // used only for search bar, not form input
  let cleanedStr = "";
  for (let i = 0; i < str.length; i++) 
  {
	  let c = str[i];
	  if( isAlpha(c) || isNumeric(c) || c == ' ')
    {
	    cleanedStr += c;
	  }
  }
  return cleanedStr;
}

function filterList() {
  let input = CleanString(document.getElementById("searchInput").value.toLowerCase());
  let items = document.querySelectorAll(".list-box .item");

  items.forEach(item => {
    item.style.display = item.textContent.toLowerCase().includes(input)
      ? "block"
      : "none";
  });
}

// --- table builder --- 
function buildTable(columns, data) {
  const header = document.getElementById("tableHeader");
  const body = document.getElementById("tableBody");

  header.innerHTML = "";
  body.innerHTML = "";

  columns.forEach(col => {
      const th = document.createElement("th");
      th.textContent = col.label;
      header.appendChild(th);
  });

  data.forEach(row => {
      const tr = document.createElement("tr");

      columns.forEach(col => {
          const td = document.createElement("td");
          td.textContent = row[col.key] ?? "";
          tr.appendChild(td);
        });

        body.appendChild(tr);
    });
}

// --- Dynamic Form ---
let currentType = null;

const formConfigs = {
  Users: [
    { key: "User_ID", label: "ID (existing to update)", type: "number" },
    { key: "Email", label: "Email", type: "text" },
    { key: "User_Type", label: "User Type (patient/doctor/admin)", type: "text" },
    { key: "Password", label: "Password", type: "text" },
  ],
  Administrators: [
    { key: "Admin_ID", label: "ID (update only)", type: "number" },
    { key: "First_Name", label: "First Name", type: "text" },
    { key: "Last_Name", label: "Last Name", type: "text" },
    { key: "Dept_ID", label: "Department ID", type: "number" },
  ],
  Doctors: [
    { key: "Doctor_ID", label: "ID (update only)", type: "number" },
    { key: "First_Name", label: "First Name", type: "text" },
    { key: "Last_Name", label: "Last Name", type: "text" },
    { key: "Specialization", label: "Specialization", type: "text" },
  ],
  Patients: [
    { key: "Patient_ID", label: "ID (update only)", type: "number" },
    { key: "First_Name", label: "First Name", type: "text" },
    { key: "Last_Name", label: "Last Name", type: "text" },
    { key: "Address", label: "Address", type: "text" },
    { key: "Phone", label: "Phone", type: "text" },
  ],
  Departments: [
    { key: "Dept_ID", label: "ID (existing to update)", type: "number" },
    { key: "Dept_name", label: "Name", type: "text" },
    { key: "Dept_head", label: "Head", type: "text" },
    { key: "Doctor_ID", label: "Doctor ID", type: "number" },
  ],
  MedicalRecords: [
    { key: "Record_ID", label: "ID (existing to update)", type: "number" },
    { key: "Patient_ID", label: "Patient ID", type: "number" },
    { key: "Doctor_ID", label: "Doctor ID", type: "number" },
    { key: "Symptoms", label: "Symptoms", type: "text" },
    { key: "Diagnosis", label: "Diagnosis", type: "text" },
  ],
  Appointments: [
    { key: "Appt_ID", label: "ID (existing to update)", type: "number" },
    { key: "Doctor_ID", label: "Doctor ID", type: "number" },
    { key: "Patient_ID", label: "Patient ID", type: "number" },
    { key: "Date", label: "Date (YYYY-MM-DD)", type: "text" },
    { key: "Time", label: "Time (HH:MM)", type: "text" },
  ],
  Rooms: [
    { key: "Room_ID", label: "ID (existing to update)", type: "number" },
    { key: "Appt_ID", label: "Appointment ID", type: "number" },
    { key: "room_type", label: "Type", type: "text" },
  ],
  Treatments: [
    { key: "Treatment_ID", label: "ID (existing to update)", type: "number" },
    { key: "Record_ID", label: "Record ID", type: "number" },
    { key: "Medicine", label: "Medicine", type: "text" },
    { key: "Prescription", label: "Prescription", type: "text" },
  ],
  Bills: [
    { key: "Payment_ID", label: "ID (existing to update)", type: "number" },
    { key: "Patient_ID", label: "Patient ID", type: "number" },
    { key: "Date", label: "Date (YYYY-MM-DD)", type: "text" },
    { key: "Cost", label: "Cost", type: "number" },
    { key: "Paid", label: "Paid (Yes/No)", type: "text" },
  ],
};

function renderForm(type) {
  currentType = type;
  const fields = formConfigs[type] || [];
  const container = document.getElementById("formFields");
  const title = document.getElementById("formTitle");
  
  title.textContent = `Edit/Add: ${type}`;
  container.innerHTML = "";

  fields.forEach(f => {
    const label = document.createElement("label");
    label.textContent = f.label;
    const input = document.createElement("input");
    input.type = f.type || "text";
    input.name = f.key;
    input.placeholder = f.label;
    container.appendChild(label);
    container.appendChild(input);
  });
}

function submitRecord() {
  if (!currentType) return;
  const container = document.getElementById("formFields");
  const inputs = container.querySelectorAll("input");

  const payload = {};
  inputs.forEach(i => {
    payload[i.name] = (i.value || "").trim();
  });

  fetch(`/api/records/${currentType}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  })
    .then(r => r.json())
    .then(_res => {
    DisplayRecords(currentType);
  });
}

function DisplayRecords(type){
    let columns = [];

    switch(type){
      case "Users":
        columns = [
          {key: "User_ID", label: "ID"},
          {key: "Email", label: "Email"},
          {key: "User_Type", label: "Type"}
        ];
        fetch("/api/users").then(r => r.json()).then(data => buildTable(columns, data));
        break;
      case "Administrators":
        columns = [
          {key: "Admin_ID", label: "ID"},
          {key: "First_Name", label: "First Name"},
          {key: "Last_Name", label: "Last Name"},
          {key: "Dept_ID", label: "Department"}
        ];
        fetch("/api/administrators").then(r => r.json()).then(data => buildTable(columns, data));
        break;
      case "Departments":
        columns = [
          {key: "Dept_ID", label: "ID"},
          {key: "Dept_name", label: "Name"},
          {key: "Dept_head", label: "Head"},
          {key: "Doctor_ID", label: "Doctor ID"}
        ];
        fetch("/api/departments").then(r => r.json()).then(data => buildTable(columns, data));
        break;
    case "MedicalRecords":
        columns = [
          {key: "Record_ID", label: "ID"},
          {key: "Patient_ID", label: "Patient"},
          {key: "Doctor_ID", label: "Doctor"},
          {key: "Symptoms", label: "Symptoms"},
          {key: "Diagnosis", label: "Diagnosis"}
        ];
        fetch("/api/medical_records").then(r => r.json()).then(data => buildTable(columns, data));
        break;
    case "Bills":
        columns = [
          {key: "Payment_ID", label: "ID"},
          {key: "Patient_ID", label: "Patient"},
          {key: "Date", label: "Date"},
          {key: "Cost", label: "Cost"},
          {key: "Paid", label: "Paid"}
        ];
        fetch("/api/bills").then(r => r.json()).then(data => buildTable(columns, data));
        break;
    case "Treatments":
        columns = [
          {key: "Treatment_ID", label: "ID"},
          {key: "Medicine", label: "Medicine"},
          {key: "Perscription", label: "Perscription"}
        ];
        fetch("/api/treatments").then(r => r.json()).then(data => buildTable(columns, data));
        break;
  case "Rooms":
    columns = [
      { key: "Room_ID", label: "ID" },
      { key: "Appt_ID", label: "Appointment" },
      { key: "room_type", label: "Type" }
    ];
    fetch("/api/rooms").then(r => r.json()).then(data => buildTable(columns, data));
    break;
  case "Appointments":
    columns = [
      { key: "Appt_ID", label: "ID" },
      { key: "Doctor_ID", label: "Doctor" },
      { key: "Patient_ID", label: "Patient" },
      { key: "Date", label: "Date" },
      { key: "Time", label: "Time" }
    ];
    fetch("/api/appointments").then(r => r.json()).then(data => buildTable(columns, data));
    break;
  case "Doctors":
    columns = [
      { key: "Doctor_ID", label: "ID" },
      { key: "First_Name", label: "First Name" },
      { key: "Last_Name", label: "Last Name" },
      { key: "Specialization", label: "Specialization" }
    ];
    fetch("/api/doctors").then(r => r.json()).then(data => buildTable(columns, data));
    break;

  case "Patients":
    columns = [
        { key: "Patient_ID", label: "ID" },
        { key: "First_Name", label: "First Name" },
        { key: "Last_Name", label: "Last Name" }
      ];
      fetch("/api/patients").then(r => r.json()).then(data => buildTable(columns, data));
      break;
  }


  renderForm(type);
}

class AppTopbar extends HTMLElement {
    connectedCallback() {
      this.innerHTML = `
        <div class="topbar2">
          <div class="topbar_logo2"><h1>Hospital.com</h1></div>
          <div class="topbar_elements">
            <div class="dropdown">
              <button class="btn_dropdown"></button>
              <div class="dropdown-content">
                <a href="/home">Home Page</a>
                <button class="btn_login" onclick="window.location.href='/logout'">Log Out</button>
              </div>
            </div>
          </div>
        </div>`;
    }
  }
  customElements.define('app-topbar', AppTopbar);

// --- Patient quick scheduling ---
function scheduleAutoAppointment() {
  fetch("/api/appointments/auto", { method: "POST" })
    .then(r => r.json())
    .then(res => {
      if (res && (res.status === "created" || res.status === "exists")) {
        alert(`Appointment scheduled on ${res.Date} at ${res.Time} with Dr. ${res.Doctor_Name}.`);
      } else if (res && res.error) {
        alert(`Failed to schedule: ${res.error}`);
      } else {
        alert("Failed to schedule appointment.");
      }
    })
    .catch(() => alert("Network error scheduling appointment."));
}
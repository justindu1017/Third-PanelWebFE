// if choose ip => disable domainName and enable ip
document.querySelector("#UseIP").addEventListener("change", () => {
  document.querySelector("#domainName").value = "";
  document.querySelector("#domainName").disabled = true;
  for (const i of document.querySelectorAll(".ipClass")) {
    i.disabled = false;
  }
});

// if choose UseDomain => enable domainName and disable ip
document.querySelector("#UseDomain").addEventListener("change", () => {
  document.querySelector("#domainName").disabled = false;
  for (const i of document.querySelectorAll(".ipClass")) {
    i.value = "";
    i.disabled = true;
  }
});

//  switch to the next input if reach the length of input
document.querySelectorAll(".number").forEach(function (el) {
  // force enter number
  function onInputNum(e) {
    // if (
    //   ((e.which != 8 && e.which != 0 && e.which < 48 && e.which != 13) ||
    //     e.which > 57) &&
    //   this.id != "domainName"
    // ) {
    //   e.preventDefault();
    // }

    // switch to next input
    if (this.value.length >= this.maxLength && this.id != "port") {
      currerentTag = this;

      while (
        currerentTag.nextElementSibling ||
        currerentTag.parentElement.parentElement.nextElementSibling
      ) {
        if (
          currerentTag.nextElementSibling &&
          (currerentTag.nextElementSibling.tagName.toLowerCase() === "input" ||
            currerentTag.nextElementSibling.tagName.toLowerCase() === "button")
        ) {
          currerentTag = currerentTag.nextElementSibling;

          window.setTimeout(() => currerentTag.focus(), 0);
          break;
        } else if (
          !currerentTag.nextElementSibling &&
          !currerentTag.parentElement.parentElement.nextElementSibling.querySelector(
            "#DomainSec"
          )
        ) {
          currerentTag =
            currerentTag.parentElement.parentElement.parentElement.nextElementSibling.querySelector(
              "input"
            );
          window.setTimeout(() => currerentTag.focus(), 0);
          break;
        } else {
          currerentTag = currerentTag.nextElementSibling;
        }
      }
    }
  }

  // if selecting an input section, select all text
  function selectAllInput(e) {
    this.select();
  }

  el.addEventListener("keyup", onInputNum.bind(el));
  el.addEventListener("focus", selectAllInput.bind(el));
});

// for 送出 BTN
var openmodal = document.querySelector(".modal-open");
openmodal.addEventListener("click", function (e) {
  e.preventDefault();
  if (checkValue()) {
    toggleModal();
  }
});

const overlay = document.querySelector(".modal-overlay");
overlay.addEventListener("click", toggleModal);

var closemodal = document.querySelectorAll(".modal-close");
for (var i = 0; i < closemodal.length; i++) {
  closemodal[i].addEventListener("click", toggleModal);
  closemodal[i].addEventListener("click", clearNode);
}

function clearNode(e) {
  const modalDiv = document.querySelector(".modalDiv");
  while (modalDiv.lastElementChild) {
    modalDiv.removeChild(modalDiv.lastElementChild);
  }
}

document.onkeydown = function (evt) {
  evt = evt || window.event;
  var isEscape = false;
  if ("key" in evt) {
    isEscape = evt.key === "Escape" || evt.key === "Esc";
  } else {
    isEscape = evt.keyCode === 27;
  }
  if (isEscape && document.body.classList.contains("modal-active")) {
    clearNode();
    toggleModal();
  }
};

function toggleModal() {
  clearNode();

  const modal = document.querySelector(".modal");
  const modalDiv = document.querySelector(".modalDiv");
  modal.classList.toggle("opacity-0");
  modal.classList.toggle("pointer-events-none");
  if (document.querySelector("#UseIP").checked) {
    ipLists = document.querySelectorAll(".ipClass");
    let newDiv = document.createElement("div");
    newDiv.innerHTML = "IP Address: ";
    newDiv.classList.add("text-2xl");
    modalDiv.appendChild(newDiv);

    for (const [index, el] of ipLists.entries()) {
      let newDiv = document.createElement("span");
      newDiv.innerHTML = el.value;
      newDiv.classList.add("text-2xl");
      modalDiv.appendChild(newDiv);
      if (!(index == ipLists.length - 1)) {
        newDiv = document.createElement("span");
        newDiv.innerHTML = ".";
        newDiv.classList.add("text-2xl");
        modalDiv.appendChild(newDiv);
      }
    }
  }

  if (document.querySelector("#UseDomain").checked) {
    let newDiv = document.createElement("div");
    newDiv.innerHTML = "Domain Name: ";
    newDiv.classList.add("text-2xl");
    modalDiv.appendChild(newDiv);
    newDiv = document.createElement("span");
    newDiv.innerHTML = document.querySelector("#domainName").value;
    newDiv.classList.add("text-2xl");
    modalDiv.appendChild(newDiv);
  }
  let newDiv = document.createElement("div");
  newDiv.innerHTML =
    "Meter Type: " + document.querySelector("#meterType").value;
  newDiv.classList.add("text-2xl");
  modalDiv.appendChild(newDiv);
  newDiv = document.createElement("div");
  newDiv.innerHTML = "Port: " + document.querySelector("#port").value;
  newDiv.classList.add("text-2xl");
  modalDiv.appendChild(newDiv);
}

function checkValue() {
  let msg = "";
  if (document.querySelector("#UseIP").checked) {
    ipLists = document.querySelectorAll(".ipClass");
    for (const [index, el] of ipLists.entries()) {
      const ipVal = el.value;
      if (ipVal == "" || ipVal.length > 3 || ipVal > 255) {
        msg += "請確認ip的第" + (index + 1) + "欄\n";
      }
    }
    const meterType = document.querySelector("#meterType").value;
    if (meterType == "") {
      msg += "請確認Meter Type\n";
    }
    const portVal = document.querySelector("#port").value;
    if (portVal.length > 5 || portVal > 65534 || portVal < 0 || portVal == "") {
      msg += "請確認port\n";
    }
    if (msg) {
      msg += "是否正確";
      alert(msg);
      return false;
    }
  }

  if (document.querySelector("#UseDomain").checked) {
    const domainVal = document.querySelector("#domainName").value;

    if (domainVal == "") {
      msg += "請確認domain name\n";
    }
    const portVal = document.querySelector("#port").value;

    if (portVal.length > 5 || portVal > 65534 || portVal < 0 || portVal == "") {
      msg += "請確認port\n";
    }
    const health_check = document.querySelector("#health_check").value;

    if (health_check == "") {
      msg += "請確認檢查間距 \n";
    }
    if (msg) {
      msg += "是否正確";

      alert(msg);
      return false;
    }
  }
  return true;
}

function submitForm(e) {
  document.querySelector("form").submit();
}

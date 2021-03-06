const overlay = document.querySelector(".modal-overlay");
overlay.addEventListener("click", toggleModal);

var closemodal = document.querySelectorAll(".modal-close");
for (var i = 0; i < closemodal.length; i++) {
  closemodal[i].addEventListener("click", toggleModal);
}

var openmodal = document.querySelector(".modal-open");
openmodal.addEventListener("click", function (e) {
  e.preventDefault();
  if (checkValue()) {
    toggleModal();
  }
});

document.onkeydown = function (evt) {
  evt = evt || window.event;
  var isEscape = false;
  if ("key" in evt) {
    isEscape = evt.key === "Escape" || evt.key === "Esc";
  } else {
    isEscape = evt.keyCode === 27;
  }
  if (isEscape && document.body.classList.contains("modal-active")) {
    toggleModal();
  }
};

function toggleModal() {
  const modal = document.querySelector(".modal");
  const modalDiv = document.querySelector(".modalDiv");
  modal.classList.toggle("opacity-0");
  modal.classList.toggle("pointer-events-none");
}

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

function delIP(ip) {
  console.log(ip);
  fetch("del/" + ip, {
    method: "DELETE",
  }).then((response) => {
    window.location.href = window.location.href;
  });
}

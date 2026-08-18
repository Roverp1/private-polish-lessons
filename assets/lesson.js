"use strict";

document.querySelectorAll("[data-quiz]").forEach(function (quiz) {
  var buttons = Array.from(quiz.querySelectorAll("[data-answer]"));
  var feedback = quiz.querySelector("[data-feedback]");
  var expected = quiz.dataset.correct;

  buttons.forEach(function (button) {
    button.addEventListener("click", function () {
      if (quiz.dataset.answered === "true") return;

      var isCorrect = button.dataset.answer === expected;
      var correctButton = buttons.find(function (candidate) {
        return candidate.dataset.answer === expected;
      });

      quiz.dataset.answered = "true";
      quiz.classList.add(isCorrect ? "is-correct" : "is-wrong");
      button.dataset.state = isCorrect ? "correct" : "wrong";
      button.setAttribute("aria-pressed", "true");

      if (!isCorrect && correctButton) {
        correctButton.dataset.state = "correct";
      }

      buttons.forEach(function (candidate) {
        candidate.disabled = true;
      });

      if (feedback) {
        var result = feedback.querySelector("[data-result]");
        if (result) {
          result.textContent = isCorrect ? "Dobrze." : "Nie tym razem.";
        }
        feedback.hidden = false;
        feedback.setAttribute("role", "status");
      }

      updateProgress();
    });
  });
});

function updateProgress() {
  var quizzes = Array.from(document.querySelectorAll("[data-quiz]"));
  var answered = quizzes.filter(function (quiz) {
    return quiz.dataset.answered === "true";
  }).length;

  document.querySelectorAll("[data-lesson-progress]").forEach(function (progress) {
    progress.max = quizzes.length;
    progress.value = answered;
  });

  document.querySelectorAll("[data-progress-text]").forEach(function (label) {
    label.textContent = "Odpowiedzi: " + answered + " z " + quizzes.length;
  });
}

document.querySelectorAll("[data-reset-quizzes]").forEach(function (button) {
  button.addEventListener("click", function () {
    document.querySelectorAll("[data-quiz]").forEach(function (quiz) {
      quiz.dataset.answered = "false";
      quiz.classList.remove("is-correct", "is-wrong");

      quiz.querySelectorAll("[data-answer]").forEach(function (answer) {
        answer.disabled = false;
        answer.removeAttribute("data-state");
        answer.setAttribute("aria-pressed", "false");
      });

      var feedback = quiz.querySelector("[data-feedback]");
      if (feedback) {
        feedback.hidden = true;
        feedback.removeAttribute("role");
      }
    });

    updateProgress();
    var firstQuiz = document.querySelector("[data-quiz]");
    if (firstQuiz) firstQuiz.scrollIntoView({ block: "center" });
  });
});

updateProgress();

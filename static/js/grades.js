/**
 * Grade Calculation System
 * Handles grade input, calculation of totals, and real-time updates
 */

document.addEventListener('DOMContentLoaded', function () {
  const courseSelect = document.getElementById('courseSelect');
  const periodSelects = document.querySelectorAll('.period-select');
  const gradeInputs = document.querySelectorAll('.grade-input');
  const resultDiv = document.getElementById('grade-result');
  let currentCourseId = courseSelect ? courseSelect.value : null;

  /**
   * Handle course selection change
   * Only navigate for professor dashboard, not for secretary
   */
  if (courseSelect) {
    courseSelect.addEventListener('change', function () {
      currentCourseId = this.value;
      // Only navigate if this is the professor dashboard
      // Secretary dashboard handles navigation in its own code
      if (window.location.pathname.includes('/professor/')) {
        window.location.href = '?course_id=' + currentCourseId;
      }
    });
  }

  /**
   * Update selected period display
   */
  periodSelects.forEach(select => {
    select.addEventListener('change', function () {
      document.getElementById('selectedPeriod').textContent = 'Période: ' + this.value;
      highlightActivePeriod(this.value);
    });
  });

  /**
   * Highlight the active period columns in the table
   */
  function highlightActivePeriod(period) {
    // This could highlight the input field for the selected period
    gradeInputs.forEach(input => {
      if (input.dataset.period === period) {
        input.style.backgroundColor = '#e3f2fd';
      } else {
        input.style.backgroundColor = '';
      }
    });
  }

  /**
   * Calculate all totals for a student
   * Total 1 = 1èP + 2èP + EXA1
   * Total 2 = 3èP + 4èP + EXA2
   * Total General = Total 1 + Total 2
   * Percentage = (Total General / somme des maxima) * 100
   */
  function calculateTotals(studentId) {
    const row = document.querySelector(`[data-student-id="${studentId}"]`);
    if (!row) return;

    const getGrade = (period) => {
      const input = row.querySelector(`input[data-period="${period}"]`);
      return input ? parseFloat(input.value) || 0 : 0;
    };

    const p1 = getGrade('1èP');
    const p2 = getGrade('2èP');
    const exa1 = getGrade('EXA1');
    const p3 = getGrade('3èP');
    const p4 = getGrade('4èP');
    const exa2 = getGrade('EXA2');

    // Calculate totals
    const total1 = p1 + p2 + exa1;
    const total2 = p3 + p4 + exa2;
    const totalGeneral = total1 + total2;

    const maxPeriods = ['1èP', '2èP', 'EXA1', '3èP', '4èP', 'EXA2'];
    const totalMax = maxPeriods.reduce((sum, period) => {
      const input = row.querySelector(`input[data-period="${period}"]`);
      const max = input ? parseFloat(input.dataset.max || input.max || '0') : 0;
      return sum + (isNaN(max) ? 0 : max);
    }, 0);
    const percentage = totalMax > 0 ? (totalGeneral / totalMax) * 100 : 0;

    // Update display
    row.querySelector('.total1').textContent = isNaN(total1) ? '0' : total1.toFixed(2);
    row.querySelector('.total2').textContent = isNaN(total2) ? '0' : total2.toFixed(2);
    row.querySelector('.totalGeneral').textContent = isNaN(totalGeneral) ? '0' : totalGeneral.toFixed(2);
    row.querySelector('.percentage').textContent = isNaN(percentage) ? '0%' : percentage.toFixed(1) + '%';

    // Color code the percentage
    const percentageSpan = row.querySelector('.percentage');
    if (percentage >= 80) {
      percentageSpan.style.color = 'green';
    } else if (percentage >= 60) {
      percentageSpan.style.color = 'orange';
    } else if (percentage > 0) {
      percentageSpan.style.color = 'red';
    }
  }

  /**
   * Show notification message
   */
  function showNotification(message, type = 'success') {
    resultDiv.innerHTML = `<div class="alert alert-${type} alert-dismissible fade show" role="alert">
      ${message}
      <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    </div>`;
    setTimeout(() => { resultDiv.innerHTML = ''; }, 3000);
  }

  /**
   * Save grade to database
   */
  async function saveGrade(studentId, period, value) {
    try {
      const response = await fetch('/professor/grade', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          student_id: parseInt(studentId, 10),
          period: period,
          value: parseFloat(value),
          course_id: currentCourseId
        })
      });
      const data = await response.json();
      if (!data.success) {
        showNotification(`Erreur: ${data.error}`, 'danger');
      }
    } catch (error) {
      showNotification('Erreur de communication avec le serveur', 'danger');
      console.error('Error:', error);
    }
  }

  /**
   * Handle grade input changes
   */
  gradeInputs.forEach(input => {
    input.addEventListener('change', async function () {
      const studentId = this.dataset.studentId;
      const period = this.dataset.period;
      const value = this.value;

      // Calculate totals immediately
      calculateTotals(studentId);

      // Save to database if value is not empty
      if (value && value.trim() !== '') {
        const maxAllowed = parseFloat(this.dataset.max) || 20;
        if (parseFloat(value) > maxAllowed) {
          this.value = '';
          calculateTotals(studentId);
          this.focus();
          showNotification(`Valeur invalide : la note maximale pour ${period} est ${maxAllowed}. Recommencez la saisie avec une valeur correcte.`, 'danger');
          return;
        }

        showNotification(`Note enregistrée pour ${period}`);
        await saveGrade(studentId, period, value);
      }
    });

    input.addEventListener('input', function () {
      const studentId = this.dataset.studentId;
      calculateTotals(studentId);
    });
  });

  /**
   * Initialize totals on page load
   */
  document.querySelectorAll('tbody tr[data-student-id]').forEach(row => {
    const studentId = row.dataset.studentId;
    calculateTotals(studentId);
  });
});


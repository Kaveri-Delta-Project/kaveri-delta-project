const buttons = document.querySelectorAll('.alphabet button');
const groups = document.querySelectorAll('.letter-group');

buttons.forEach(button => {
  button.addEventListener('click', () => {
    const letter = button.dataset.letter;

    // Hide all letter sections
    groups.forEach(group => {
      group.classList.remove('active');
    });

    // Show the selected one
    const target = document.getElementById('letter-' + letter);
    if (target) {
      target.classList.add('active');
    }
  });
});

document.addEventListener('click', function (e) {
  const header = e.target.closest('.item-header');
  if (!header) return;

  const item = header.parentElement;
  item.classList.toggle('open');
});
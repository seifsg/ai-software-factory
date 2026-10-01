import {normalizeTitle, readTasks} from './model.mjs';

const form = document.getElementById('task-form');
const input = document.getElementById('title');
const feedback = document.getElementById('feedback');
const list = document.getElementById('tasks');
const empty = document.getElementById('empty');
const tasks = readTasks(localStorage);

function render() {
  list.replaceChildren(...tasks.map(title => {
    const item = document.createElement('li');
    item.textContent = title;
    return item;
  }));
  empty.hidden = tasks.length > 0;
}

form.addEventListener('submit', event => {
  event.preventDefault();
  const title = normalizeTitle(input.value);
  if (!title) {
    feedback.textContent = 'Enter a task title.';
    input.focus();
    return;
  }
  try {
    localStorage.setItem('task-notes', JSON.stringify([...tasks, title]));
  } catch {
    feedback.textContent = 'Your task could not be saved. Please try again.';
    return;
  }
  tasks.push(title);
  render();
  input.value = '';
  feedback.textContent = 'Task added.';
  input.focus();
});

render();

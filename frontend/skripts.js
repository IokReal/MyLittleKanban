const DEBUG = true;
const testData = window.testData;
var tasksData = [];
var currentMovingTaskName = null;
var currentTargetTabForNewTask = null;
var selectedProject = null;

function render() {
    const tabsContainer = document.getElementById("tabs");
    tabsContainer.innerHTML = "";

    const templateContainer = document.getElementById("tamplate");
    const tabTemplateHtml = templateContainer.querySelector(".tab").outerHTML;
    const taskTemplateHtml = templateContainer.querySelector(".task").outerHTML;

    tasksData.forEach(tab => {
        let allTasksHtml = "";
        tab.tasks.forEach(task => {
            let taskHtml = taskTemplateHtml
                .replaceAll("{tasks_name}", task.tasks_name)
                .replace("{text}", task.text);

            allTasksHtml += taskHtml;
        });

        let tabHtml = tabTemplateHtml
            .replaceAll("{tab_name}", tab.tab_name)
            .replace(taskTemplateHtml, allTasksHtml);

        tabsContainer.insertAdjacentHTML("beforeend", tabHtml);
    });
}

function updateDialog() {
    const form = document.getElementById("move_dialog_select");
    form.innerHTML = '<option value="" disabled selected>Выберите колонку...</option>';

    tasksData.forEach(tab => {
        form.innerHTML += `<option value="${tab.tab_name}">${tab.tab_name}</option>`;
    });
}

function muveTask(buttonElement) {
    currentMovingTaskName = buttonElement.dataset.taskName;
    updateDialog();
    const move_dialog = document.getElementById("move_dialog");
    move_dialog.showModal();
}

function confirmMoveTask() {
    const select = document.getElementById("move_dialog_select");
    const targetTabName = select.value;

    if (!targetTabName || !currentMovingTaskName) return;

    let movedTask = null;

    tasksData.forEach(tab => {
        const taskIndex = tab.tasks.findIndex(t => t.tasks_name === currentMovingTaskName);
        if (taskIndex !== -1) {
            movedTask = tab.tasks.splice(taskIndex, 1)[0];
        }
    });

    if (movedTask) {
        const targetTab = tasksData.find(tab => tab.tab_name === targetTabName);
        if (targetTab) {
            targetTab.tasks.push(movedTask);
        }
    }

    document.getElementById("move_dialog").close();
    currentMovingTaskName = null;
    render();
}

// 1. Открытие модального окна создания задачи
function openAddTaskDialog(buttonElement) {
    currentTargetTabForNewTask = buttonElement.dataset.tabName;

    // Очищаем инпуты
    document.getElementById("new_task_name").value = "";
    document.getElementById("new_task_text").value = "";

    document.getElementById("add_task_dialog").showModal();
}

// 2. Добавление новой задачи в массив
function confirmAddTask(event) {
    event.preventDefault();

    const name = document.getElementById("new_task_name").value.trim();
    const text = document.getElementById("new_task_text").value.trim();

    if (!name || !currentTargetTabForNewTask) return;

    // Находим нужный таб и добавляем карточку
    const targetTab = tasksData.find(tab => tab.tab_name === currentTargetTabForNewTask);
    if (targetTab) {
        targetTab.tasks.push({
            "tasks_name": name,
            "text": text
        });
    }

    document.getElementById("add_task_dialog").close();
    currentTargetTabForNewTask = null;
    render();
}

// 3. Создание новой колонки (таба)
function addNewTab() {
    const tabName = prompt("Введите название новой колонки:");
    if (!tabName) return;

    const exists = tasksData.some(tab => tab.tab_name.toLowerCase() === tabName.trim().toLowerCase());
    if (exists) {
        alert("Колонка с таким названием уже существует!");
        return;
    }

    tasksData.push({
        "tab_name": tabName.trim(),
        "tasks": []
    });

    render();
}

// 4. проэкт
function selectProject() {
    const projectSelect = document.getElementById("project_select");

    if (DEBUG) {
        const selectedProject = testData.find(
            prj => prj.projectName === projectSelect.value
        );

        if (selectedProject) {
            tasksData = selectedProject.data;
        }
    }

    render();
}

async function updateSelectProject() {
    const projectSelect = document.getElementById("project_select");
    const selectedValue = projectSelect.value;

    projectSelect.innerHTML = "";

    if (DEBUG) {
        testData.forEach(project => {
            const option = document.createElement("option");

            option.value = project.projectName;
            option.textContent = project.projectName;

            projectSelect.appendChild(option);
        });
    }

    if (selectedValue) {
        projectSelect.value = selectedValue;
    }
}

async function init() {
    "use strict";
    tasksData = testData[0]["data"];
    updateSelectProject()
    render();
}
const testData = [
    {
        "tab_name": "test name 1",
        "tasks":[
            {
                "tasks_name":"tdk task1",
                "text":"bla bla bla"
            },
            {
                "tasks_name":"second task2",
                "text":"another text"
            }
        ]
    },
    {   
        "tab_name": "test name 2",
        "tasks":[
            {   
                "tasks_name":"tdk task3",
                "text":"bla bla bla"
            },
            {
                "tasks_name":"second task4",
                "text":"another text"
            }
        ]
    },
];

var tasksData = [];
var currentMovingTaskName = null;
var currentTargetTabForNewTask = null; // Запоминаем, в какой таб добавляем задачу

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
            .replace("{tab_name}", tab.tab_name)
            .replace("{tab_name}", tab.tab_name) // На случай, если {tab_name} встречается несколько раз в шаблоне
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

// ---------------- ПОДОБРАННЫЕ ФУНКЦИИ ДОБАВЛЕНИЯ ----------------

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
    event.preventDefault(); // Предотвращаем перезагрузку страницы при отправке формы

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

    // Проверяем, нет ли уже колонки с таким именем
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

async function init(){
    "use strict";
    tasksData = testData;
    render();
}
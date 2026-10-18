var tasksData = [];
var currentMovingTaskId = null; // Переименовано для ясности (хранит ID)
var currentTargetTabForNewTask = null;
var selectedProject = null;
var selectedTaskId = null;
var selectedTabId = null;

class RULE_TYPE {
    ROOT = 0
    PROJ_OWN = 1
    READ_PROJ = 2
    WRITE_PROJ = 3
    READ_GROUP = 4
    WRITE_GROUP = 5
    DELETE_PROJECT_GROUP = 6
    MANAGE_MEMBERS = 7
    READ_TASK = 8
    WRITE_TASK = 9
    DELETE_TASK = 10
}

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
                .replaceAll("{task_id}", task.task_id)
                .replaceAll("{tasks_name}", task.tasks_name)
                .replace("{text}", task.text);

            allTasksHtml += taskHtml;
        });

        let tabHtml = tabTemplateHtml
            .replaceAll("{task_group_id}", tab.tab_id)
            .replaceAll("{tab_name}", tab.tab_name)
            .replace(taskTemplateHtml, allTasksHtml);

        tabsContainer.insertAdjacentHTML("beforeend", tabHtml);
    });
}

function updateDialog() {
    const form = document.getElementById("move_dialog_select");
    form.innerHTML = '<option value="" disabled selected>Выберите колонку...</option>';

    tasksData.forEach(tab => {
        // Используем tab_id в качестве value
        form.innerHTML += `<option value="${tab.tab_id}">${tab.tab_name}</option>`;
    });
}

function muveTask(buttonElement) {
    currentMovingTaskId = Number(buttonElement.dataset.taskId);
    updateDialog();
    document.getElementById("move_dialog").showModal();
}

function confirmMoveTask() {
    const select = document.getElementById("move_dialog_select");
    const targetTabId = Number(select.value);

    if (!targetTabId || !currentMovingTaskId) return;

    let movedTask = null;

    // Ищем и вырезаем задачу по ID
    tasksData.forEach(tab => {
        const taskIndex = tab.tasks.findIndex(t => t.task_id === currentMovingTaskId);
        if (taskIndex !== -1) {
            movedTask = tab.tasks.splice(taskIndex, 1)[0];
        }
    });

    // Добавляем в целевую колонку по ID
    if (movedTask) {
        const targetTab = tasksData.find(tab => tab.tab_id === targetTabId);
        if (targetTab) {
            targetTab.tasks.push(movedTask);
        }
    }

    document.getElementById("move_dialog").close();
    currentMovingTaskId = null;
    render();
}

// 1. Открытие модального окна создания задачи
function openAddTaskDialog(buttonElement) {
    currentTargetTabForNewTask = buttonElement.dataset.tabId;
    document.getElementById("new_task_name").value = "";
    document.getElementById("new_task_text").value = "";
    document.getElementById("add_task_dialog").showModal();
}

// 2. Добавление новой задачи в массив
async function confirmAddTask(event) {
    event.preventDefault();

    const name = document.getElementById("new_task_name").value.trim();
    const text = document.getElementById("new_task_text").value.trim();

    if (!name || !currentTargetTabForNewTask) return;

    try {
        const response = await fetch(`/api/v1/groups/${currentTargetTabForNewTask}/add_task`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name: name, text: text })
        });

        if (!response.ok) throw new Error("Не удалось создать задачу на сервере");

        document.getElementById("add_task_dialog").close();
        currentTargetTabForNewTask = null;
        await selectProject();
    } catch (error) {
        console.error(error);
        alert("Ошибка при создании задачи");
    }
}


// 4. Проект
async function selectProject() {
    const projectSelect = document.getElementById("project_select");
    selectedProject = projectSelect.value;

    if (!selectedProject) return;

    try {
        const groupsRes = await fetch(`/api/v1/projects/${selectedProject}/groups`);
        if (!groupsRes.ok) throw new Error("Не удалось загрузить группы");
        const groups = await groupsRes.json();

        const tasksRes = await fetch(`/api/v1/projects/${selectedProject}/tasks`);
        if (!tasksRes.ok) throw new Error("Не удалось загрузить задачи");
        const tasks = await tasksRes.json();

        tasksData = groups.map(group => ({
            tab_id: group[0],
            tab_name: group[1],
            tasks: tasks.filter(t => t[3] === group[0]).map(t => ({
                task_id: t[0],
                tasks_name: t[1],
                text: t[2],
                order: t[3]
            }))
            .sort((a, b) => a.order - b.order)
        }));

        render();
    } catch (error) {
        console.error(error);
        document.getElementById('cannot_loadPproject_data_dialog').showModal();
    }
}

async function updateSelectProject() {
    const projectSelect = document.getElementById("project_select");
    projectSelect.innerHTML = '<option value="" disabled selected>Загрузка проектов...</option>';

    try {
        const response = await fetch('/api/v1/user/projects');
        if (!response.ok) throw new Error("Ошибка авторизации или загрузки");
        
        const projects = await response.json();
        
        projectSelect.innerHTML = '<option value="" disabled selected>Выберите проект...</option>';
        
        projects.forEach(project => {
            const option = document.createElement("option");
            option.value = project[0];
            option.innerText = project[1];
            projectSelect.appendChild(option);
        });
    } catch (error) {
        console.error(error);
        projectSelect.innerHTML = '<option value="" disabled selected>Ошибка загрузки</option>';
    }
}

function openAddTabDialog() {
    document.getElementById("new_tab_name").value = "";
    document.getElementById("addNewTab_dialog").showModal();
}

async function confirmAddTab(event) {
    event.preventDefault();

    const tabNameInput = document.getElementById("new_tab_name");
    const tabName = tabNameInput.value.trim();

    if (!tabName) return;

    try {
        const response = await fetch(`/api/v1/projects/${selectedProject}/add_group`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name: tabName })
        });

        if (!response.ok) throw new Error("Не удалось создать колонку на сервере");

        document.getElementById("addNewTab_dialog").close();
        await selectProject();
    } catch (error) {
        console.error(error);
        alert("Ошибка при создании колонки");
    }
}
async function validSesion() {
    const response = await fetch('/api/v1/user/display_name');
    if (response.status === 401){
        window.location.href = "/login";
        await new Promise(r => setTimeout(r, 100));
    }
}
function edit_task(button) {
    console.log(button);
    selectedTaskId = Number(button.dataset.task_id);
    document.getElementById('editTask_dialog').showModal();
}

async function delet_task() {
    if (!selectedTaskId) return;

    try {
        const res = await fetch(`/api/v1/tasks/${selectedTaskId}`, { method: 'DELETE' });
        if (res.status === 401) {
            window.location.href = "/login";
            return;
        }
        if (!res.ok) throw new Error("HTTP " + res.status);

        document.getElementById('editTask_dialog').close();
        selectedTaskId = null;
        await selectProject();   // перезагрузить доску
    } catch (error) {
        console.error(error);
        alert("Не удалось удалить задачу");
    }
}

function delete_tab_prompt(button) {
    selectedTabId = Number(button.dataset.tabId);
    if (confirm("Вы действительно хотите удалить эту колонку со всеми задачами?")) {
        delet_tab();
    }
}

async function delet_tab() {
    if (!selectedTabId) return;

    try {
        const res = await fetch(`/api/v1/groups/${selectedTabId}`, { method: 'DELETE' });
        if (res.status === 401) {
            window.location.href = "/login";
            return;
        }
        if (!res.ok) throw new Error("HTTP " + res.status);

        selectedTabId = null;
        await selectProject(); // Перезагрузить доску
    } catch (error) {
        console.error(error);
        alert("Не удалось удалить колонку");
    }
}

function openAddProjectDialog() {
    document.getElementById("new_project_name").value = "";
    document.getElementById("new_project_desc").value = "";
    document.getElementById("addNewProject_dialog").showModal();
}

async function confirmAddProject(event) {
    event.preventDefault();

    const name = document.getElementById("new_project_name").value.trim();
    const desc = document.getElementById("new_project_desc").value.trim();

    if (!name) return;

    try {
        const response = await fetch('/api/v1/projects', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name: name, description: desc })
        });

        if (!response.ok) {
            const errText = await response.text();
            throw new Error(errText || "Не удалось создать проект");
        }

        const data = await response.json();

        document.getElementById("addNewProject_dialog").close();

        await updateSelectProject();
        const projectSelect = document.getElementById("project_select");
        projectSelect.value = data.project_id;
        await selectProject();

    } catch (error) {
        console.error(error);
        alert("Ошибка при создании проекта: " + error.message);
    }
}

async function delet_Project() {
    if (!selectedProject) {
        alert("Проект не выбран");
        return;
    }

    if (!confirm("Вы действительно хотите удалить этот проект со всеми колонками и задачами?")) {
        return;
    }

    try {
        const res = await fetch(`/api/v1/projects/${selectedProject}`, { method: 'DELETE' });
        
        if (res.status === 401) {
            window.location.href = "/login";
            return;
        }
        if (!res.ok) throw new Error("HTTP " + res.status);

        document.getElementById('manegeProject_dialog').close();
        
        selectedProject = null;

        await updateSelectProject();
        
        const projectSelect = document.getElementById("project_select");
        if (projectSelect.options.length > 1) {
            projectSelect.selectedIndex = 1;
            await selectProject();
        } else {
            tasksData = [];
            render();
        }

    } catch (error) {
        console.error(error);
        alert("Не удалось удалить проект");
    }
}

async function init() {
    "use strict";
    await validSesion();

    await updateSelectProject();
    
    const projectSelect = document.getElementById("project_select");
    if (projectSelect.options.length > 1) {
        projectSelect.selectedIndex = 1;
        await selectProject();
    }
}
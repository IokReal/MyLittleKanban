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
            .replace(taskTemplateHtml, allTasksHtml); 

        tabsContainer.insertAdjacentHTML("beforeend", tabHtml);
    });
}

async function updateDialog() {
    const form = document.getElementById("move_dialog_select");
    form.innerHTML = "";
    tasksData.forEach(tab => {
        form.innerHTML += '<option value="">' + tab["tab_name"] +'</option>';
    })
}

async function muveTask(buttonElement) {
    updateDialog()
    const move_dialog = document.getElementById("move_dialog");
    const taskName = buttonElement.dataset.taskName;
    console.log("Кликнули по задаче:", taskName);
    move_dialog.showModal();
}

async function init(){
    "use strict";
    tasksData = testData;
    render();
}

const searchField = document.querySelector("#searchField");
const appTable = document.querySelector(".app-table");
const paginationContainer = document.querySelector(".pagination-container");
const tableOutput = document.querySelector('.table-output');
tableOutput.style.display = "none";
const tbody = document.querySelector(".table-body");
const noResults = document.querySelector(".no-results");

searchField.addEventListener('keyup', (e)=>{
    const searchValue = e.target.value;
    if (searchValue.trim().length > 0){
        paginationContainer.style.display = "none";
        tbody.innerHTML = "";
        fetch('/search-expenses', {
            body: JSON.stringify({ searchText: searchValue }),
            method: "POST",
        })
        .then((res) => res.json())
        .then((data) => {
            appTable.style.display = "none";
            tableOutput.style.display = "block";
            if(data.length === 0){
                noResults.style.display = "block";
                tableOutput.style.display = "none";
            }else{
                noResults.style.display = "none";
                data.forEach((item) => {
                    tbody.innerHTML += `
                        <tr>
                        <td>${item.amount}</td>
                        <td>${item.category}</td>
                        <td>${item.description}</td>
                        <td>${item.date}</td>
                        </tr>`;
                });
            }   
        });
    }else{
        tableOutput.style.display = "none";
        appTable.style.display = "block";
        paginationContainer.style.display = "block";
    }
});    
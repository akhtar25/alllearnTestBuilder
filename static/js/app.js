// Replace with your own values
const searchClient = algoliasearch(
    'RVHAVJXK1B',
    '052fb99bb2ad2b2b180a48c5f5c352df' // search only API key, not admin API key
  );
  
  const search = instantsearch({
    indexName: 'prd_course',
    searchClient,
    routing: true,
    insightsClient: window.aa,
  });
  	
  search.addWidgets([
instantsearch.widgets.pagination({
    container: '#pagination',
    showFirst: false,
    showPrevious: true,
    showNext: true,
    showLast: false,
    padding: 4,
   
    templates: {
        first: '«',
        previous: '‹',
        next: '›',
        last: '»',
      },
  })
]);
  search.addWidgets([
    instantsearch.widgets.configure({
      hitsPerPage: 12,
    })
  ]);
  search.addWidgets([
    instantsearch.widgets.configure({
      clickAnalytics: true,
    })
 ]);
  search.addWidgets([
    instantsearch.widgets.searchBox({
      container: '#search-box',
      placeholder: 'Search for topics',
      searchAsYouType: false,
      showReset: false,
      showSubmit: false,
      showLoadingIndicator: true,
    })
  ]);
  
  search.addWidgets([
    instantsearch.widgets.hits({
      container: '#hits',
      sortBy: ['course_name:asc'],
      templates: {
        item(item) {
          return `               
            <div class="hit-data card small hoverable section" style="border-radius: 25px;">
                <div class="card-image waves-effect waves-block waves-light">
                    <img class="activator" style="border-radius: 25px;"
                        src="${item.image_url}">
                </div>
                <div class="card-content">
                    <span class="card-title activator grey-text text-darken-4">
                        <h4>${item.course_name}</h4><i class="material-icons right">more_vert</i>
                    </span>
                    <h5 class="grey-text">${item.teacher_name}</h5>                   
                    <a href="/courseDetail?courseID=${item.course_id}"><span class="right" style="font-size: small;">Go
                            to
                            Course</span></a>
                </div>
                <div class="card-reveal">
                    <span class="card-title grey-text text-darken-4"><h4>${item.course_name}</h4><i
                            class="material-icons right">close</i></span>
                    <p style="width: 80%;font-size:16px">${item.average_rating}<span class="stars">${item.average_rating}</span><br>
                    ${item.description}
                    </p>

                    <p><a href="/courseDetail?courseID=${item.course_id}"><span class="right"
                                style="font-size: small;">Go to
                                Course</span></a></p>
                </div>
            </div>        
          `;
        },
        empty(results) {
            return `<h3 class='grey-text'>No results for <q>${results.query}</q></h3>`;
          }
      }  
    })
  ]);
  search.start();
  
// Replace with your own values
const searchClient = algoliasearch(
    'RVHAVJXK1B',
    '052fb99bb2ad2b2b180a48c5f5c352df' // search only API key, not admin API key
  );
  
  const search = instantsearch({
    indexName: 'staging_COURSE',
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
      sortBy: ['topic_name:asc'],
      templates: {
        item(item) {
          return `

            <a href="/courseDetail?courseID=${item.topic_id}"><div class="card small hoverable  z-depth-0" style="border-radius: 25px;">
            <div class="card-image waves-effect waves-block waves-light">
                <img class="activator" style="border-radius: 5px;" src="../static/images/chris-barbalis-oOBMoCOgGrY-unsplash.jpg">
            </div>
            <div class="card-content">
                <span class="card-title activator grey-text text-darken-4"><h4>${item.topic_name}</h4></span>
                <h5>Course Name</h5>
                <h5 class="grey-text">Shailesh Vishwakarma</h5>                         
            </div></a>

            <button class="right btn" style="background-color: transparent; ${
              instantsearch.insights('clickedObjectIDsAfterSearch', {
                eventName: 'Add to favorite',
                objectIDs: [item.objectID]
              })
            }>
            <i
            class="material-icons right green-text" style="font-size:medium">favorite_border</i>
            </button>         
          `;


        },
        empty(results) {
            return `<h3 class='grey-text'>No results for <q>${results.query}</q></h3>`;
          }
      }
  
    })
  ]);
  
  
  search.start();
  
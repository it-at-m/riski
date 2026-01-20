# Programmatic query of the RIS

The RIS has some special features that make programmatic use difficult.
We do not yet fully understand and know these, but we will nevertheless briefly outline the current state of knowledge with which we have been successful.

## Network analysis browser

To gain an initial understanding of the system, we tried to use the browser's network analysis.
It is important to note that requests using other tools sometimes deliver different results.
This is good for a rough overview of how it works and which requests are actually sent, but not good for
precise planning of the script.
This is particularly helpful because most buttons on the page do not have hrefs behind them, but instead redirect or load via some JS functions.
In our case, this allowed us to determine the requests for navigation in the list, which otherwise would not have been found.

## SessionID

When a new client requests the RIS for the first time, i.e., without cookies and SessionID, it receives a new ID from the server and a redirect to a URL that also contains the SessionID.
This is also where the “StateID” is set for the first time and, at least in our observations, starts at 0.

## Cookies

In addition to the SessionID, 4 cookies are also delivered with the first request. We were unable to determine exactly what these cookies are relevant for in our work, but we included them anyway to be on the safe side.

## HTTP 302

The RIS stores a lot of state for the users, although it is not entirely clear how this works exactly.
One of the main implications of this management is that the RIS increments an “ID” per session under which
the state can be accessed at a specific point in time.
In the vast majority of cases, the RIS therefore responds with HTTP 302 and specifies the link with the new
ID to the state that has just been changed as the location. As a rule, either “Follow-Redirects” must be set to TRUE,
or manual following must be implemented.

## “Internal page” IDs

In addition to the ID for the state, there are also other IDs on the individual pages that are incremented and influence usage.
For example, this link can be used to adjust the results per page: <https://risi.muenchen.de/risi/sitzung/uebersicht?37-5.0-list_container-list-card-cardheader-itemsperpage_dropdown_top>
The 37 is the “state ID” and the 5 is a page-specific ID. We have not been able to determine the exact rules for when this second ID is incremented.
Experience has shown that it is also incremented by 1 with every state-changing request, but this has not been confirmed.
However, we do know that the corresponding links can be found in the HTML of the page. This method can therefore be used to determine the currently valid and functioning URL.

```javascript
Wicket.Event.add(window, "domready", function(event) {
Wicket.Ajax.ajax({"u":"./uebersicht?9-2.0-form-periodeButton-periodenEintrag-0-periode","c":"id33","e":"click","pd":true});;
Wicket.Ajax.ajax({"u":"./uebersicht?9-2.0-form-periodeButton-periodenEintrag-1-periode","c":"id34","e":"click","pd":true});;
Wicket.Ajax.ajax({"u":"./uebersicht?9-2.0-form-periodeButton-periodenEintrag-2-periode","c":"id35","e":"click","pd":true});;
Wicket.Ajax.ajax({"u":"./uebersicht?9-2.0-form-periodeButton-periodenEintrag-3-periode","c":"id36","e":"click","pd":true});;
Wicket.Ajax.ajax({"u":"./uebersicht?9-2.0-form-periodeButton-periodenEintrag-4-periode","c":"id37","e":"click","pd":true});;
Wicket.Ajax.ajax({"u":"./uebersicht?9-2.0-list_container-list-card-cardheader-sort_filter","m":"POST","c":"id8","e":"change"});;
Wicket.Ajax.ajax({"u":"./uebersicht?9-2.0-list_container-list-card-cardheader-nav_top-navigation-1-pageLink","c":"id38","e":"click","pd":true});;
Wicket.Ajax.ajax({"u":"./uebersicht?9-2.0-list_container-list-card-cardheader-nav_top-navigation-2-pageLink","c":"id39","e":"click","pd":true});;
Wicket.Ajax.ajax({"u":"./uebersicht?9-2.0-list_container-list-card-cardheader-nav_top-next","c":"idb","e":"click","pd":true});;
Wicket.Ajax.ajax({"u":"./uebersicht?9-2.0-list_container-list-card-cardheader-nav_top-last","c":"idc","e":"click","pd":true});;
Wicket.Ajax.ajax({"u":"./uebersicht?9-2.0-list_container-list-card-cardheader-itemsperpage_dropdown_top","m":"POST","c":"idd","e":"change"});;
Wicket.Ajax.ajax({"u":"./uebersicht?9-2.0-list_container-list-card-cardfooter-nav_bottom-navigation-1-pageLink","c":"id3a","e":"click","pd":true});;
Wicket.Ajax.ajax({"u":"./uebersicht?9-2.0-list_container-list-card-cardfooter-nav_bottom-navigation-2-pageLink","c":"id3b","e":"click","pd":true});;
Wicket.Ajax.ajax({"u":"./uebersicht?9-2.0-list_container-list-card-cardfooter-nav_bottom-next","c":"id10","e":"click","pd":true});;
Wicket.Ajax.ajax({"u":"./uebersicht?9-2.0-list_container-list-card-cardfooter-nav_bottom-last","c":"id11","e":"click","pd":true});;
Wicket.Ajax.ajax({"u":"./uebersicht?9-2.0-list_container-list-card-cardfooter-itemsperpage_dropdown_bottom","m":"POST","c":"id12","e":"change"});;
Wicket.Event.publish(Wicket.Event.Topic.AJAX_HANDLERS_BOUND);
```

## Filtering the session list

To filter the session list, there is a form in the WebUI where you can set the start, end, status, and type of the session.
This form triggers a POST request. You can also send this POST request programmatically and receive a redirect to the page with the
corresponding filters set.
In the code, we have to execute the filter request twice to get the correct redirect URL.
Only one filter request was necessary via Postman/Bruno. It is not clear where this discrepancy comes from.
If you now execute a GET request on the redirect URL, you will get the page with the corresponding active filtering.

Edit 06/26/2025: Further testing determined that the initial request in the code did not arrive correctly at the RIS. The response was HTTP 503. As a result,
the first valid request was only sent to the RIS with the filter request, and thus the redirect URL at this point was also the one with the session ID. After adjusting the code, a correct initial request is sent and only one filter request is necessary.

## AJAX reloading

The RIS reloads content more frequently via AJAX, especially in the session list. However, the data is loaded directly as an HTML fragment, which is then integrated into the page.
This means that it is neither raw data nor correct HTML. The data is available in an XML structure and the “new” HTML is a value in this structure.
To simulate the reloading of data, it is important that the correct headers are set, otherwise the RIS will simply deliver the first page.
In our experience, the header “Wicket-Ajax:true” must be set. We have also set the following headers because they were also set in the browser

```text
Wicket-Ajax-BaseURL:sitzung/uebersicht?4
Wicket-FocusedElementId:idb
X-Requested-With:XMLHttpRequest
Priority:u=0
```

## Persistence of the state

We had the problem that our state was sometimes not permanently retained. For example, if we set the number of results per page
to 100 and then filtered the session list, this setting was reset to 10. If we filtered first and then increased it to 100, it worked,
so you may need to experiment a little.
Bruno was quite helpful with all these tests.

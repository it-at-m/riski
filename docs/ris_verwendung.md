# Programmatische Anfrage des RIS

Das RIS bringt einige Besonderheiten mit sich, die die programmatische Verwendung erschweren.
Diese sind uns noch nicht vollständig verständlich und bekannt, hier soll jedoch trotzdem kurz der aktuelle Wissensstand skizziert werden, mit dem wir erfolgreich waren.

## Netzwerkanalyse Browser

Für ein erstes Verständnis des Systems haben wir versucht die Netzwerkanalyse des Browsers zu verwenden.
Wichtig ist hierbei, dass die Requests bei Verwendung andere Tools teilweise andere Ergebnisse liefern.
Für einen groben Überblick, wie das so ungefähr funktioniert und welche Requests überhaupt abgesetzt werden gut, für
eine genaue Planung des Skripts nicht gut.
Das ist vor allem hilfreich weil die meisten Buttons auf der Seite hrefs dahinter haben sondern über irgendwelche JS-Funktionen weiterleiten oder laden.
In unserem Fall haben wir darüber die Requests für die Navigation in der Liste ermitteln können, die sonst eher nicht gefunden worden wären.

## SessionID

Bei erstmaligem Anfragen des RIS durch einen neuen Client, also ohne Cookies und SessionID, erhält dieser eine neue ID vom Server und einen Redirect zu einer URL in der ebenfalls die SessionID steht.
Hier wird auch die "StateID" das erste mal gesetzt und beginnt, zumindest in unseren Beobachtungen, bei 0.

## Cookies

Neben der SessionID werden beim ersten Request auch noch 4 Cookies mitgeliefert. Wofür diese Cookies genau relevant sind haben wir bei unseren Arbeiten nicht erkennen können, aber wir haben sie sicherheitshalber mal mitgenommen.

## HTTP 302

Das RIS speichert sehr viel State für die User, wobei nicht ganz klar ist, wie das genau abläuft.
Eine der Hauptimplikationen dieses Managements ist es, dass das RIS eine "ID" pro Session hochzählt, unter der
der State zu einem bestimmten Zeitpunkt erreichbar ist.
Das RIS antwortet daher in extrem vielen Fällen mit HTTP 302 und gibt als Location den Link mit der neuen
ID zu dem State den man gerade geändert hat an. In der Regel muss also entweder "Follow-Redirects" auf TRUE gesetzt werden,
oder ein manuelles Folgen implementiert werden.

## "Seiteninterne" IDs

Neben der ID für den State gibt es auch auf den einzelnen Seiten weitere IDs, die hochgezählt werden und die Verwendung beeinflussen.
Für die Anpaasung der Ergebnisse pro Seite gibt es bspw. diesen Link: <https://risi.muenchen.de/risi/sitzung/uebersicht?37-5.0-list_container-list-card-cardheader-itemsperpage_dropdown_top>
Die 37 ist hierbei die "State-ID" und die 5 eine Seitenspezifische ID. Die genauen Regeln wann diese zweite hochgezählt wird haben wir nicht ermitteln können.
Erfahrungsgemäß wird diese mit jedem State verändernden Request ebenfalls um 1 hochgezählt, das ist aber nicht sicher belegt.
Wir wissen jedoch, dass sich die entsprechenden Links im HTML der Seite finden lassen. Über diesen Weg kann also die aktuell gültige und funktionierende URL ermittelt werden.

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

## Filterung der Sitzungsliste

Um die Sitzungsliste zu filtern gibt es in der WebUI ein Formular über das Start, Ende, Status und Art der Sitzung gesetzt werden können.
Diese Formular löst einen POST-Request aus. Diesen POST-Request kann man auch programmatisch abschicken und erhält einen Redirect zu der Seite mit den
entsprechend gesetzten Filtern.
Im Code müssen wir den Filter Request doppelt ausführen, damit wir die korrekte Redirect URL erhalten.
Über Postman/Bruno war nur ein Filter Request notwendig. Woher diese Diskrepanz kommt ist nicht klar.
Wenn man nun einen GET Request auf die Rediret URL ausführt erhält man die Seite mit der entsprechenden aktiven Filterung.

Edit 26.06.2025: Bei weiteren Tests wurde ermittelt, dass der initiale Request im Code nicht richtig beim RIS ankam. Die Antwort war HTTP 503. Dadurch wurde
erst mit dem Filterrequest der erste valide Request an das RIS geschickt und somit war auch dir Redirect URL an dieser Stelle die mit der Session ID. Nach Anpassung des Codes wird ein korrekter Initialer Request geschickt und es ist nur noch ein Filter Request notwendig.

## AJAX Nachladen

Das RIS lädt Inhalte häufiger über AJAX nach, insbesondere in der Sitzungsliste. Hierbei werden die Daten jedoch direkt als HTML Fragment geladen, welches dann in die Seite eingebunden wird.
Es handelt sich damit also weder um Rohdaten noch um korrektes HTML. Die Daten liegen in einer XML-Struktur vor und das "neue" HTML ist ein Value in dieser Struktur.
Um das Nachladen der Daten nachzustellen ist es wichtig, dass die korrekten Header gesetzt werden, da das RIS sonst einfach die erste Seite ausliefert.
Nach unserer Erfahrung muss der Header "Wicket-Ajax:true" gesetzt werden. Wir haben außerdem folgende Header gesetzt, weil diese auch im Browser gesetzt waren:

```text
Wicket-Ajax-BaseURL:sitzung/uebersicht?4
Wicket-FocusedElementId:idb
X-Requested-With:XMLHttpRequest
Priority:u=0
```

## Persistenz des States

Wir hatten das Problem, dass unser State teilweise nicht dauerhaft mitgenommen wurde. Wenn wir also zum Beispiel die Anzahl der Ergebnisse pro Seite
auf 100 gesetzt haben und danach die Sitzungsliste gefiltert haben wurde diese Einstellung wieder auf 10 resettet. Wenn erst gefiltert und dann auf 100 erhöht wurde hat das geklappt,
daher muss man ggf. etwas experimentieren.
Für diese ganzen Tests war Bruno recht hilfreich.

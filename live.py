import json
import xml.etree.ElementTree as ET
import urllib
import math
import time
import sys
import keys

ZWS_KEY = keys.ZWS_KEY 
EDU_KEY = keys.EDU_KEY 
NCDC_KEY = keys.NCDC_KEY 

# mean
#
# Calculates the arithmetic mean of a list of numbers
#
# Parameters:
#   listOfNumbers: the list of numbers for which the mean should be calculated
#
# Return value: the arithmetic mean of the given numbers
def mean(listOfNumbers):
    mean = -1.0
    sum = 0.0
    count = len(listOfNumbers)
    for number in listOfNumbers:
        sum += number
    if count > 0:
        mean = sum/count
    return mean

# median
#
# Calculates the median of a sorted list of numbers
#
# Parameters:
#   sortedListOfNumbers: a sorted list of numbers for which the median should be
#       calculated
#
# Return value: the median of the given numbers
# If the list is empty, this returns -1.0
def median(sortedListOfNumbers):  
    median = -1.0
    count = len(sortedListOfNumbers)
    if count % 2 == 1:
        median = sortedListOfNumbers[count/2]
    elif count > 0:
        first = sortedListOfNumbers[count/2]
        second = sortedListOfNumbers[count/2 + 1]
        median = (first + second)/2
    return median

# getRange
#
# Calculates the range of a sorted list of numbers
# 
# (Calling it "range" would conflict with Python's range function)
#
# Parameters:
#   sortedListOfNumbers: a sorted list of numbers for which the range should be
#       calculated
#
# Return value: the range of the list of numbers
# If the list is empty, this returns -1.0
def getRange(sortedListOfNumbers):
    range = -1.0
    count = len(sortedListOfNumbers)
    if count > 0:
        range = sortedListOfNumbers[count-1] - sortedListOfNumbers[0]
    return range

# stdDevS
#
# Calculates the standard deviation of a sample. Standard deviation of a sample
# is defined as sqrt((1/N) * the sum from i=1 to N of (x sub i - x bar)^2).
# (I think in LaTeX that would be
#   s = \sqrt{\frac{1}{N-1} \sum_{i=1}^N (x_i - \overline{x})^2} )
#
# Parameters:
#   listOfNumbers: a sample of numbers for which the standard deviation should
#       be calculated
#
# Return value: the standard deviation of the sample
# If the list is empty, this returns -1.0
def stdDevS(listOfNumbers):
    stddev = -1.0
    count = len(listOfNumbers)
    if count > 1:
        stddev = 0.0
        theMean = mean(listOfNumbers)
        for number in listOfNumbers:
            stddev += (number - theMean)**2
        stddev /= count - 1
        stddev = math.sqrt(stddev)
    return stddev

# latLon
#
# Gets the latitude and longitude for a city from the Zillow web service
#
# Parameters:
#   city: the name of the city for which to get the latitude and longitude
#   state: the state in which the city is
#
# Return value: a list with the first member being the latitude and the second
#   member being the longitude
# In the case of a non-successful lookup, [0.0, 0.0] is returned
def latLon(city, state):
    latLon = [0.0, 0.0]
    demoRequest = urllib.urlopen("http://www.zillow.com/webservice/" + 
            "GetDemographics.htm?zws-id=" + ZWS_KEY + "&city=" + city +
            "&state=" + state)
    demoXML = ET.parse(demoRequest).getroot()
    # API defines 0 as success
    if demoXML.find("message").find("code").text != "0":
        return latLon
    latLon[0] = demoXML.find("response").find("region").find("latitude").text
    latLon[1] = demoXML.find("response").find("region").find("longitude").text
    return latLon

# getZIPs
#
# Gets the ZIP codes for a given city from redline13's API
#
# Parameters:
#   city: the name of the city for which to find ZIP codes
#   state: the state in which the city is
#
# Return value: a list of zip codes for the given city 
def getZIPs(city, state):
    zipRequest = urllib.urlopen("http://zipcodedistanceapi.redline13.com/rest/" 
            + "city-zips.json/" + city + "/" + state)
    zipJSON = json.load(zipRequest)
    return zipJSON["zip_codes"]

# weather
#
# Gets information on weather of a given city from the NOAA API. Groups the
# information into seasons. Looks up data from the year 2008.
#
# (I am not a fan on the way I wrote this)
#
# Parameters:
#   city: the name of the city for which to get weather information
#   state: the state in which the city is
#
# Return value: a string containing the weather information (formatted in HTML)
def weather(city, state):
    def nameOf(NOAACode):
        try:
            name = str(seasonInfo.names[str(NOAACode)])
        except KeyError:
            name = str(NOAACode)
        return name
    def formatData(dataType, value):
        pointOnes = ["CLDD", "MNTM", "EMXT", "EMNT", "MMXT", "MMNT"]
        toFahr = ["MNTM", "EMXT", "EMNT", "MMXT", "MMNT"]
        name = nameOf(dataType)
        if dataType in pointOnes:
            value *= 0.1
        if dataType in toFahr:
            value *= 1.8
            value += 32.0
        return ("<strong>" + name + ":</strong> " + str(round((value), 2)))

    # seasonInfo
    #
    # Averages monthly weather data within a given season. The data is from the
    # 2008 NOAA data.
    #
    # Parameters
    #   zip: the zip code for which to find the weather data
    #   seasonCode: the number corresponding with the season for which the
    #       weather should be found. 1 is Winter, 2 is Spring, 3 is Summer, and
    #       4 is Fall.
    #
    # Return value: a string containing the weather information. Formatted with
    #   HTML.
    def seasonInfo(zip, seasonCode, attempt):
        seasonToMonth = [[12, 1, 2], [3, 4, 5], [6, 7, 8], [9, 10, 11]]
        dCollection = {"DT90":0}
        for monthCode in seasonToMonth[seasonCode]:
            time.sleep(1)
            theURL = ("http://www.ncdc.noaa.gov/cdo-services/services/datasets/"
                    + "GHCNDMS/locations/ZIP:" + str(zip) + "/data.json?year="
                    + "2008&month=" + str(monthCode) + "&token=" + NCDC_KEY)
            monthRequest = urllib.urlopen(theURL)
            monthJSON = json.load(monthRequest)
            data = monthJSON["dataCollection"]["data"]
            for datum in data:
                key = datum["dataType"][0]
                dCollection[key] = dCollection.get(key, 0) + datum["value"]
        
        seasonHTML = "<p>"
        for key in dCollection.keys():
            val = 1.0*dCollection[key]/len(seasonToMonth[seasonCode])
            seasonHTML += (formatData(key, val) + "<br>\n")
        seasonHTML += "</p>"
        return seasonHTML
    # Setting it as a property of the function because apparently Python doesn't
    # have "static"
    seasonInfo.names = {"MMXT":"Mean max temp", "MMNT":"Mean min temp",
        "EMXT":"Max temp", "EMNT":"Min temp",
        "MNTM":"Mean temp", "HTDD":"Heating degree days",
        "CLDD":"Cooling Degree Days", "BMXT":"Highest", "BMNT": "Lowest",
        "DT90":"Days w/ max over 90", "DX32":"Days w/ max under 32",
        "DT32":"Days w/ min under 32", "DT00":"Days w/ min under 0",
        "TPCP":"Total precip", "BMXP":"Greatest observed precip",
        "TSNW":"Total snow fall", "MXSD":"Max. snow depth",
        "DP01":"Days >0.1\" precip", "DP05":"Days >0.5\" precip",
        "DP10":"Days >1.0\" precip", "EMXP":"Max daily precip"}
    zipNdx = 0
    zips = getZIPs(city, state)
    weatherHTML = "<h2>Weather info</h2>\n"
    seasons = ["Winter", "Spring", "Summer", "Fall"]
    for i in range(4):
        seasonHTML = ""
        # This loop's purpose is to find the weather data for the first zip code
        # for the city that actually has weather data associated with it
        exceptionThrown = True
        while exceptionThrown and zipNdx < len(zips):
            try:
                seasonHTML = seasonInfo(zips[zipNdx], i, 0)
                exceptionThrown = False
            except TypeError:
                zipNdx += 1
        weatherHTML += ("<h3>" + seasons[i] + " monthly averages</h3>\n" +
                seasonHTML)
    return weatherHTML

# zillowMortgage
#
# Gets info from the Zillow web service about mortgages in a given state
#
# Parameters:
#   state: the state for which mortgage data should be found
#
# Return value: a string containing mortgage information (formatted with HTML)
# On non-success, returns the message information from the API
def zillowMortgage(state):
    mortgageRequest = urllib.urlopen("http://www.zillow.com/webservice/" + 
        "GetRateSummary.htm?zws-id=" + ZWS_KEY + "&state=" + state +
        "&output=json")
    mortgage = json.load(mortgageRequest)
    if mortgage["message"]["code"] != "0":# API defines "0" as success
        return "<p>zillowMortgage: " + mortgage["message"]["text"] + "</p>"
    lastWeek = mortgage["response"]["lastWeek"]
    mortgageHTML = ("<h2>Mortgages in " + state + "</h2>\n" +
                    "<p><strong>30 year fixed rate loans:</strong> " +
                    lastWeek["thirtyYearFixed"] + "% (from " + 
                    lastWeek["thirtyYearFixedCount"] + " quotes)</p>\n" +
                    "<p><strong>15 year fixed rate loans:</strong> " +
                    lastWeek["fifteenYearFixed"] + "% (from " +
                    lastWeek["fifteenYearFixedCount"] + " quotes)</p>\n" +
                    "<p><strong>5/1 adjustable rate loans:</strong> " +
                    lastWeek["fiveOneARM"] + "% (from " +
                    lastWeek["fiveOneARMCount"] + " quotes)</p>\n" +
                    "<p>See <a href=\"http://www.zillow.com/mortgage-rates/\">"
                    + "mortgage rates</a> on Zillow</p>")
    return mortgageHTML

# schoolRatings
#
# Gets school rating information from the education.com API
#
# Parameters:
#   city: the city for which to find school ratings
#   state: the state in which the city is
#
# Return value: a string containing school ratings information (formatted with
#   HTML) 
def schoolRatings(city, state):
    rateRequest = urllib.urlopen("http://api.education.com/service/service.php?"
            + "f=getTestRating&key=" + EDU_KEY + "&sn=sf&v=4&city=" + city +
            "&state=" + state + "&Resf=json")
    ratingsList = []
    ratings = json.load(rateRequest)
    for schoolObj in ratings:
        try:
            school = schoolObj["school"]
            if school["testrating_text"] != "":
                spaceSplit = school["testrating_text"].split(" ")
                aRating = int(spaceSplit[len(spaceSplit)-1])
                ratingsList.append(aRating)
        except TypeError:
            pass
    ratingsList.sort()
    rateHTML = "<h2>School ratings (1-10)</h2>\n"
    rateHTML += ("<p><strong>Number of ratings:</strong> " + 
            str(len(ratingsList)) + "<br>\n" + 
            "<strong>Arithmetic mean:</strong> " +
            str(round(mean(ratingsList), 3)) + "<br>\n" +
            "<strong>Standard deviation:</strong> " +
            str(round(stdDevS(ratingsList), 3)) + "<br>\n" +
            "<strong>Median:</strong> " + str(median(ratingsList)) + "<br>\n" +
            "<strong>Range:</strong> " + str(getRange(ratingsList)) + "</p>")
    return rateHTML

# zillowDemographics
#
# Gets some demographics information about a given city from the Zillow web
# service
#
# Parameters:
#   city: the city for which to find school ratings
#   state: the state in which the city is
#
# Return value: a string containing demographics information (formatted with
#   HTML)
def zillowDemographics(city, state):
    def pageHTML(page):
        pageH = "<h2>" + page.find("name").text + "</h2>\n"
        tables = page.find("tables")
        for table in tables.findall("table"):
            pageH += tableHTML(table) + "\n"
        return pageH
    def tableHTML(table):
        if table.find("name").text not in zillowDemographics.tables:
            return ""
        tableH = ""
        for attribute in table.find("data").findall("attribute"):
            tableH += attributeHTML(attribute)
        return tableH
    def attributeHTML(attr):
        if attr.find("name").text not in zillowDemographics.names:
            return ""
        attrHTML = "<p><strong>" + attr.find("name").text + ":</strong> "
        if attr.find("values") is not None:
            values = attr.find("values")
            city = values.find("city")
            if city is not None:
                value = city.find("value")
                if value.text is not None:
                    attrHTML += value.text + "</p>"
        elif attr.find("value") is not None:
            attrHTML += attr.find("value").text + "</p>"
        return attrHTML
    
    zillowDemographics.names = ["Zillow Home Value Index",
            "Median 3-Bedroom Home Value", "Median Home Size (Sq. Ft.)",
            "Avg. Year Built", "Median Household Income",
            "Median Age"]
    zillowDemographics.tables = ["Affordability Data",
            "Homes & Real Estate Data", "People Data"]
    
    demoHTML = ""
    demoRequest = urllib.urlopen("http://www.zillow.com/webservice/GetDemogr" +
            "aphics.htm?zws-id=" + ZWS_KEY + "&city=" + city + "&state=" + state)
    demoXML = ET.parse(demoRequest).getroot()
    if demoXML.find("message").find("code").text != "0":# API defines 0 as success
        error = "<p>zillowDemographics: "
        error += demoXML.find("message").find("code").text + " "
        error += demoXML.find("message").find("text").text + "</p>"
        return error
    pages = demoXML.find("response").find("pages")
    for page in pages.findall("page"):
        demoHTML += pageHTML(page) + "\n"
    region = demoXML.find("response").find("region")
    demoHTML += ("<p><a href=\"" +
                 demoXML.find("response").find("links").find("forSale").text + 
                 "\">See " + region.find("city").text +
                 " Real Estate on Zillow</a></p>")
    return demoHTML

print "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.01//EN\"\n    \"http://www.w3.org/TR/html4/strict.dtd\">"
print "<html>"
print "<head>"
print "    <meta http-equiv=\"Content-type\" content=\"text/html;charset=UTF-8\">"
print "    <link href=\"./style.css\" rel=\"stylesheet\" type=\"text/css\">"
print "    <title>City Info</title>"
print "</head>"
print "<body>"
print "<div id=\"content\">"

for line in sys.stdin:
    cityInfo = [i.strip() for i in line.split(',')]
    if len(cityInfo) < 2:
        print "<p>Bad city name \"" + line.strip() + "\""
        break
    city = cityInfo[0]
    state = cityInfo[1].upper()
    latitudeAndLongitude = latLon(city, state)
    print "<h1>" + city.title() + ", " + state + "</h1>"
    print ("<p><a href=\"http://maps.google.com/maps?&z=12&q=loc:" +
        "+".join(latitudeAndLongitude) + "\"><img alt=\"map\" src=\"http://maps" +
        ".googleapis.com/maps/api/staticmap?sensor=false&size=400x300&zoom=8" + 
        "&markers=" + ",".join(latitudeAndLongitude) + "\"></a><br>")
    print "<strong>Location:</strong> " + ", ".join(latitudeAndLongitude) + "</p>"
    print
    print schoolRatings(city, state)
    print weather(city, state)
    print
    print zillowDemographics(city, state)
    print
    print zillowMortgage(state)

print "</div>"
print "<p>Mortgage and demographics data (c) Zillow, Inc., 2006-2013. Use is subject to <a href=\"http://www.zillow.com/corp/Terms.htm\">Terms of Use</a><br>"
print "<a href=\"http://zillow.com/\"><img src=\"http://www.zillow.com/widgets/GetVersionedResource.htm?path=/static/logos/zmm_logo_small.gif\" width=\"145\" height=\"15\" alt=\"Zillow Real Estate Search\"></a><br>"
print "<a href=\"http://www.zillow.com/wikipages/What-is-a-Zestimate/\">What's a Zestimate?</a></p>"
print "<p>Schools data provided by <a href=\"http://www.education.com/schoolfinder/\"><img src=\"http://01.edu-cdn.com/i/logo/edu-logo-75x31.jpg\" alt=\"Education.com logo\"></a><br>"
print "(c) Education.com, Inc. 2011. Use is subject to Terms of Service</p>"
print "</body>"
print "</html>"

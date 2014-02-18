# -*- coding: cp1255 -*-

from datetime     import datetime
from urllib.parse import quote, unquote
from selenium     import webdriver
from selenium.common.exceptions    import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
import random, json, re

def random_heb_sentence( length ):
    s = ""
    for x in range( length ):
        c = random.choice( heb_chars )
        is_space = random.random() <= 0.2 # 20% chance for space
        if is_space:
            s += " "
        else:
            s += c
    return s

def test_page_loaded( b, case, logfile ):
    css_selector = "input[id='send']"

    w = WebDriverWait( b, 10 )
    try:
        e = w.until(
            lambda b: b.find_element_by_css_selector( css_selector )
        )
    except TimeoutException:
        print( "*** Failed to load form with pageTitle: %s ***" % case )
        logfile.write( "\t\t***Failed to load form ***\n" )

url = "http://www.kampyle.com/feedback_form/ff-feedback-form.php?site_code=3131167&form_id=100152&lang=he&param[domain]=www.issta.co.il&param[siteSection]=non-match&param[refGclid]=false&param[utmz_timestamp]=1392628406&param[utmz_numberOfSessions]=1&param[utmz_visitSources]=1&param[utmcsr]=(direct)&param[utmccn]=(direct)&param[utmcmd]=(none)&param[sessionCounter]=1&param[cookie_k_click]=4&param[bind]=Loading%3ABindingTo_DOMContentLoaded&param[k_loadtimeMS]=4&param[hostName]=www.issta.co.il&param[pagePath]=%2F&param[pageTitle]=%D7%90%D7%99%D7%A1%D7%AA%D7%90%20-%20%D7%98%D7%99%D7%A1%D7%95%D7%AA%20%D7%9C%D7%97%D7%95%22%D7%9C%2C%20%D7%A0%D7%95%D7%A4%D7%A9%20%D7%91%D7%97%D7%95%22%D7%9C%2C%20%D7%93%D7%99%D7%9C%D7%99%D7%9D%2C%20%D7%9E%D7%9C%D7%95%D7%A0%D7%95%D7%AA%2C%20%D7%A0%D7%95%D7%A4%D7%A9%20%D7%91%D7%90%D7%A8%D7%A5&param[refHostName]=direct&param[refURL]=direct&param[refFilename]=direct&param[LandingPage]=direct&param[windowWidth]=1280&param[windowHeight]=679&param[windowSize]=1280x679&param[time_OnSite]=00%3A12%3A37&param[time_OnSiteInSecs]=757&param[time_OnSiteInMins]=12&param[buttonRev]=KB%3A19822%7CKP%3A18687%7CIssta%7CKC%3Av6.52_27Feb13&vectors=60444405010913_1392629162914&time_on_site=755&stats=k_button_js_revision%3D19822%26k_push_js_revision%3D18687%26view_percentage%3D100%26display_after%3D50&url=http%3A%2F%2Fwww.issta.co.il%2F&utmb=136873000.8.9.1392629162916&utma=136873000.694914551.1392628404.1392628406.1392628406.1"

pat =  "(.+\[pageTitle\]=)"  # everything until the "pageTitle" param
pat += "([\d\w%-]+)"         # The actual page title (value)
pat += "(&.+)"               # everything after the page title
start, page_title, end = re.match( pat, url ).groups()

heb_chars = u"אבגדהוזחטיכלמםנןסעפףצץקרשת"
eng_chars = "abcdefghijklmnopqrstuvexyz"

orig_title = u'איסתא - טיסות לחו"ל, נופש בחו"ל, דילים, מלונות, נופש בארץ'

b = webdriver.Ie()
b.set_page_load_timeout( 5 )

test_cases = {}

# open logfile for writing
logfile = open( 'logfile', 'w' ) 

# initialize test_cases
for case in [ 
    'str_length',
    'pos_of_quotemark',
    'pos_of_hypehn',
    'pos_of_comma',
    'len_quotes',
    'len_hyphens',
    'len_commas',
    'len_quotes_hyphens',
    'len_quotes_hyphens_commas',
    'original_string',
    'scrambled'
    ]:
    test_cases[ case ] = []

def build_up_title():
    build_up = ""
    for c in orig_title:
        build_up += c
        test_cases['original_string'].append( build_up )

def create_random_tests():
    ## Length
    # Create random sequence of "words" separated by spaces with a length of
    # up to 200 chars, growing by 5 chars every time
    # A space has a change of 20% to be added to the string
    for i in range(5,205,5):
        s = random_heb_sentence( i )
        test_cases['str_length'].append( s ) 

    ## Quotes
    # Quote at the begining of the sentence
    base = random_heb_sentence( 50 )
    test_cases['pos_of_quotemark'].append( '"' + base ) 

    # Quote at the end of the sentence
    test_cases['pos_of_quotemark'].append( base + '"' ) 

    # Quote at the middle of the sentence
    s = list( base )
    s.insert( round((len(s)-1)/2), '"' )
    test_cases['pos_of_quotemark'].append( "".join(s) )

    # Quote at the beginning and the end of the sentence
    test_cases['pos_of_quotemark'].append( '"' + base + '"' )

    # Quote at the beginning, middle and end of the sentence
    test_cases['pos_of_quotemark'].append( '"' + "".join(s) + '"' )

    ## Hyphens
    # Hyphen at the begining of the sentence
    base = random_heb_sentence( 50 )
    test_cases['pos_of_hypehn'].append( '-' + base ) 

    # Hyphen at the end of the sentence
    test_cases['pos_of_hypehn'].append( base + '-' ) 

    # Hyphen at the middle of the sentence
    s = list( base )
    s.insert( round((len(s)-1)/2), '-' )
    test_cases['pos_of_hypehn'].append( "".join(s) )

    # Hyphen at the beginning and the end of the sentence
    test_cases['pos_of_hypehn'].append( '-' + base + '-' )

    # Hyphen at the beginning, middle and end of the sentence
    test_cases['pos_of_hypehn'].append( '-' + "".join(s) + '-' )

    ## Commas
    # Comma at the begining of the sentence
    base = random_heb_sentence( 50 )
    test_cases['pos_of_comma'].append( ',' + base ) 

    # Comma at the end of the sentence
    test_cases['pos_of_comma'].append( base + ',' ) 

    # Comma at the middle of the sentence
    s = list( base )
    s.insert( round((len(s)-1)/2), ',' )
    test_cases['pos_of_comma'].append( "".join(s) )

    # Comma at the beginning and the end of the sentence
    test_cases['pos_of_comma'].append( ',' + base + ',' )

    # Comma at the beginning, middle and end of the sentence
    test_cases['pos_of_comma'].append( ',' + "".join(s) + ',' )

    # Length-quotes
    for i in range(5,205,5):
        s = random_heb_sentence( i )

        ## Quotes with various length strings
        # Quote at the begining of the sentence
        test_cases['len_quotes'].append( '"' + s ) 

        # Quote at the end of the sentence
        test_cases['len_quotes'].append( s + '"' ) 

        # Quote at the middle of the sentence
        l = list( s )
        l.insert( round((len(s)-1)/2), '"' )
        test_cases['len_quotes'].append( "".join(l) )

        # Quote at the beginning and the end of the sentence
        test_cases['len_quotes'].append( '"' + s + '"' )

        # Quote at the beginning, middle and end of the sentence
        test_cases['len_quotes'].append( '"' + "".join(l) + '"' )

        ## Hyphens with various length strings
        # Hyphen at the begining of the sentence
        test_cases['len_hyphens'].append( '-' + s ) 

        # Hyphen at the end of the sentence
        test_cases['len_hyphens'].append( s + '-' ) 

        # Hyphen at the middle of the sentence
        l = list( s )
        l.insert( round((len(s)-1)/2), '-' )
        test_cases['len_hyphens'].append( "".join(l) )

        # Hyphen at the beginning and the end of the sentence
        test_cases['len_hyphens'].append( '-' + s + '-' )

        # Hyphen at the beginning, middle and end of the sentence
        test_cases['len_hyphens'].append( '-' + "".join(l) + '-' )

        ## Quotes and Hyphens with various length strings
        # Quote at the beginning and a hyphen at the end
        test_cases['len_quotes_hyphens'].append( '"' + s + "-" ) 

        # Hypehn at the beginning and a quote at the end
        test_cases['len_quotes_hyphens'].append( '-' + s + '"' ) 

        # Double quotes with a hyphen in the middle
        l = list( s )
        l.insert( round((len(s)-1)/2), '-' )
        test_cases['len_quotes_hyphens'].append( '"' + "".join(l) + '"' ) 

        # Insert random 3 hyphens and 2 quotes
        p1 = random.randint( 0, len(l) - 1 )
        p2 = random.randint( 0, len(l) - 1 )

        l = list( s )
        l.insert( p1, "-" )
        l.insert( p2, '"' )

        test_cases['len_quotes_hyphens'].append( "".join(l) ) 

        # Insert random hyphens, quotes and commas
        for i in range(10):
            l = list( s )
            for c in [ "-", '"', '"', ",", ",", ",", "," ]:
                p = random.randint( 0, len(l) - 1 )
                l.insert( p, c )
            
            test_cases['len_quotes_hyphens_commas'].append( "".join(l) ) 



for i in range( 10 ):
    words = orig_title.split()
    rebuilt = []
    for i in range( len(words) ):
        w = words.pop( words.index( random.choice( words ) ) )
        rebuilt.append( w )

    new_title = " ".join( rebuilt )
    test_cases['scrambled'].append( new_title )

logfile.write( "Test starting at %s\n" % datetime.now() )
for i, tt in enumerate(test_cases):
    if tt:
        logfile.write( "\t%s. Testing %s\n" % (i,tt) )
        for j,t in enumerate(test_cases[tt]):
            title   = quote( t )
            new_url = start + title + end

            print( "%s | Testing len: %s" % ( tt, len(t) ) )
            logfile.write( "\t\t%s.%s. Testing len: %s\n" % (i,j,len(t)) )
            logfile.write( "\t\tString: %s\n" % unquote(t, encoding='cp1255') )
            logfile.write( "\t\tQuoted: %s\n" % title   )
            logfile.write( "\t\tURL: %s\n"    % new_url )
            if tt in [ 'pos_of_quotemark', 'len_quotes', 'len_quotes_hyphens' ]:
                qcount = t.count('"')
                qpos   = t.index('"')
                print( "Quotes: %s in position: %s" % ( qcount, qpos ) )
            elif tt in [ 'pos_of_hypehn', 'len_hyphens', 'len_quotes_hyphens' ]:
                qcount = t.count('-')
                qpos   = t.index('-')
                print( "Hyphens: %s in position: %s" % ( qcount, qpos ) )
            print( "\n" )

            start_time = datetime.now()

            try:
                b.get( new_url )    
            except TimeoutException:
                print( "*** Failed to load form with pageTitle: %s ***" % case )
                logfile.write( "\t\t***Failed to load form ***\n" )

            test_page_loaded( b, t.encode('cp1255'), logfile )

            end_time = datetime.now()
            dt = end_time - start_time

            logfile.write( "\t\tTime taken: %s seconds\n" % dt.seconds )

logfile.write( "\tX. Testing original url that should fail\n" )
logfile.write( "\t\tString: %s\n" % unquote(page_title) )
logfile.write( "\t\tQuoted: %s\n" % quote( page_title ) )
logfile.write( "\t\tURL: %s\n"    % url )

try:
    b.get( url )    
except TimeoutException:
    print( "*** Failed to load form with pageTitle: %s ***" % case )
    logfile.write( "\t\t***Failed to load form ***\n" )

test_page_loaded( b, 'original_url', logfile )

logfile.close()
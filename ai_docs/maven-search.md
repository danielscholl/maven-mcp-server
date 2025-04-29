# Maven Central Repository Search API

## REST API

These URLs allow you to access the search functionality of the Central Repository from any non-browser user agent. Note that the "wt" parameter present in every URL determines the format of the results. Setting "wt" equal to "json" will provide a JSON response, while setting "wt" equal to "xml" will provide the same response formatted as an XML document. Another common parameter is "rows," which limits the number of results returned by the server.

> **Note:** Most of the URLs in this document have been URL-decoded for the sake of readability. They should work when pasted into a web browser, but you may have to URL-encode them to function when called programmatically.

If you need any support, please check the section [How do I get support?](#how-do-i-get-support).

## API Endpoints

| URL | Description |
|-----|-------------|
| `https://search.maven.org/solrsearch/select?q=guice&rows=20&wt=json` | Mimics typing "guice" in the basic search box. Returns first page of artifacts with "guice" in the groupId or artifactId and lists details for most recent version released. |
| `https://search.maven.org/solrsearch/select?q=g:com.google.inject+AND+a:guice&core=gav&rows=20&wt=json` | Mimics clicking the link for all versions of groupId "com.google.inject" and artifactId "guice." Returns sorted list of all versions of an artifact. |
| `https://search.maven.org/solrsearch/select?q=g:com.google.inject&rows=20&wt=json` | Search for all artifacts in the groupId "com.google.inject." For each artifact, returns details for the most recent version released. |
| `https://search.maven.org/solrsearch/select?q=a:guice&rows=20&wt=json` | Search for any artifactId named "guice," irrespective of groupId. For each artifact returns details for the most recent version released. |
| `https://search.maven.org/remotecontent?filepath=com/jolira/guice/3.0.0/guice-3.0.0.pom` | Downloads a file at the given path from the Central Repository (https://repo1.maven.org/maven2/ and its mirrors). |
| `https://search.maven.org/solrsearch/select?q=g:com.google.inject%20AND%20a:guice%20AND%20v:3.0%20AND%20l:javadoc%20AND%20p:jar&rows=20&wt=json` | Mimics searching by coordinate in Advanced Search. This search uses all coordinates ("g" for groupId, "a" for artifactId, "v" for version, "p" for packaging, "l" for classifier) |
| `https://search.maven.org/solrsearch/select?q=c:junit&rows=20&wt=json` | Mimics searching by classname in Advanced Search. Returns a list of artifacts, down to the specific version, containing the class. |
| `https://search.maven.org/solrsearch/select?q=fc:org.specs.runner.JUnit&rows=20&wt=json` | Mimics searching by fully-qualified classname in Advanced Search. Returns a list of artifacts, down to the specific version containing the class. |
| `https://search.maven.org/solrsearch/select?q=1:35379fb6526fd019f331542b4e9ae2e566c57933&rows=20&wt=json` | Mimics searching by SHA-1 Checksum in Advanced Search. You will need to calculate the SHA-1 for the file before sending the request to the Central Repository. |
| `https://search.maven.org/solrsearch/select?q=tags:sbtplugin&rows=20&wt=json` | Mimics searching for tags:sbtplugin in the basic searchbar. |
| `https://search.maven.org/solrsearch/select?q=tags:sbtVersion-0.11&rows=20&wt=json` | Mimics searching for tags:sbtVersion-0.11 in the basic searchbar. |
| `https://search.maven.org/solrsearch/select?q=tags:scalaVersion-2.9&rows=20&wt=json` | Mimics searching for tags:scalaVersion-2.9 in the basic search bar. |

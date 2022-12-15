* Black box mode seems to generate java tests which probably should be run separately (?) or does it run it (investigate)
  * results did go to `$pwd/src/em` in my experimentation
  * Jar was located in `/`
  * run command in `eclipse-temurin:17-jre-ubi9-minimal` based image:
    * `java --add-opens java.base/java.net=ALL-UNNAMED --add-opens java.base/java.util=ALL-UNNAMED -jar /EvoMaster/evomaster.jar --blackBox true --bbSwaggerUrl https://api.apis.guru/v2/openapi.yaml --outputFormat JAVA_JUNIT_4 --maxTime 30s --ratePerMinute 60`
* add faulty target for check output

#####
Sample output: 
```sh
[root@82e64cfac77e /]# java --add-opens java.base/java.net=ALL-UNNAMED --add-opens java.base/java.util=ALL-UNNAMED -jar ./EvoMaster --blackBox true --bbSwaggerUrl https://api.apis.guru/v2/openapi.yaml --outputFormat JAVA_JUNIT_4 --maxTime 30s --ratePerMinute 60
*
 _____          ___  ___          _
|  ___|         |  \/  |         | |
| |____   _____ | .  . | __ _ ___| |_ ___ _ __
|  __\ \ / / _ \| |\/| |/ _` / __| __/ _ \ '__|
| |___\ V / (_) | |  | | (_| \__ \ ||  __/ |
\____/ \_/ \___/\_|  |_/\__,_|___/\__\___|_|


* EvoMaster version: 1.5.0
* WARNING: You are doing Black-Box testing, but you did not specify the 'problemType'. The system will default to RESTful API testing.
* Initializing...
* There are 2 usable RESTful API endpoints defined in the schema configuration
01:25:18.791 [main] WARN  o.e.core.search.StructuralElement - class org.evomaster.core.problem.rest.RestCallAction should have a parent but currently it is null
01:25:18.819 [main] WARN  o.e.c.p.rest.RestActionBuilderV3 - Unhandled format 'url'
01:25:18.820 [main] WARN  o.e.c.p.rest.RestActionBuilderV3 - No fields for object definition: info
01:25:18.820 [main] WARN  o.e.c.p.rest.RestActionBuilderV3 - No fields for object definition: externalDocs
* Starting to generate test cases
* WARNING: Schema has no info on where the API is, eg 'host' in v2 and 'servers' in v3. Going to use same location as where the schema was downloaded from
* Consumed search budget: 103.660%; covered targets: 4; time per test: 4437.1ms (4.4 actions)
* Going to save 2 tests to src/em
01:25:50.058 [main] WARN  o.e.c.o.service.HttpWsTestCaseWriter - Currently no assertions are generated for response type: text/html;charset=utf-8
* Evaluated tests: 7
* Evaluated actions: 31
* Needed budget: 100%
* Passed time (seconds): 31
* Execution time per test (ms): Avg=4437.14 , min=1084.00 , max=9882.00
* Computation overhead between tests (ms): Avg=6.00 , min=2.00 , max=14.00
* Successfully executed (HTTP code 2xx) 0 endpoints out of 2 (0%)
* EvoMaster process has completed successfully
* Use --help and visit http://www.evomaster.org to learn more about available options
```
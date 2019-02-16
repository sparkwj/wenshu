_empty_result_pattern = /^setTimeout\(\'\$\(/

function validateRunEval(runEval) {
    s = unzip(runEval);
    if (_empty_result_pattern.test(s)) {return '__NONE__';}
}

function decryptDocID(runEval, docid){
    s = unzip(runEval);
    ss = s.split(';;');
    eval(ss[0] + ';');
    ss1 = ss[1].match(/_\[_\]\[_\]\((.*?)\)\(\);/)[1]
    st = eval(ss1)
    key = st.match(/com\.str\._KEY=\"(.{32}).*?;/)[0]
    eval(key)
    var unzipid = unzip(docid);
    var realid = com.str.Decrypt(unzipid);
    return realid;
}

function decryptListContent(data) {
    var docs = [];
    try {
        datalist = eval(eval(data));
        if (datalist == undefined || datalist == null || datalist.length <= 1)
            return docs;

        dataCount = (datalist[0].Count != undefined ? datalist[0].Count : 0);
        if (dataCount == 0)
            return docs;
        else
            docs.push(parseInt(dataCount))

        if (datalist[0].RunEval != undefined) {
            s = unzip(datalist[0].RunEval);
            ss = s.split(';;');
            eval(ss[0] + ';');
            ss1 = ss[1].match(/_\[_\]\[_\]\((.*?)\)\(\);/)[1];
            st = eval(ss1);
            key = st.match(/com\.str\._KEY=\"(.{32}).*?;/)[0];
            eval(key);

            for (var i = 1; i < datalist.length; i++) {
                var doc = {};
                var item = datalist[i];
                var doc_id = item['文书ID']
                doc_id = unzip(doc_id);
                doc_id = com.str.Decrypt(doc_id);
                doc['doc_id'] = doc_id;
                doc['status'] = 0;
                doc['case_name'] = item['案件名称'];
                doc['case_no'] = item['案号'];
                doc['case_type'] = item['案件类型'];
                doc['court_name'] = item['法院名称'];
                doc['trial_date'] = item['裁判日期'];
                //doc['trial_summary'] = item['裁判要旨段原文'];
                docs.push(doc);
            }

            return docs;
        }
    } catch (ex) {
        return docs;
    }
}

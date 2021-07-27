import pandas as pd
import argparse
import subprocess
import os
import re
import time

from os import listdir
from os.path import isfile, join
from subprocess import PIPE

def get_bugs_in_file(path):
    count = 0
    with open(path, "r") as file:
        lines = file.readlines()
        for line in lines:
            if line.startswith("---"): count += 1
    return count


def get_bugs_in_repo(version, project_name):    
    tmp_project_dir = "/tmp/{project_name}".format(project_name=project_name)
    subprocess.call("rm -rf target", shell=True, cwd=tmp_project_dir)
    subprocess.call("git checkout {version}".format(version=version), shell=True, cwd=tmp_project_dir)
    # subprocess.call("mvn test", shell=True, cwd=tmp_project_dir)
    proc = subprocess.Popen("mvn test", shell=True, stdout=subprocess.PIPE, cwd=tmp_project_dir)
    stats_lines = []
        
    while True:
        line = proc.stdout.readline()
        if not line:
            break
        if "Failures: " and "Errors: " in line.decode("utf-8"):
            stats_lines.append(line.decode("utf-8"))
    
    time.sleep(2)
    if len(stats_lines) == 0:
        return -1
    stats_line = stats_lines[-1]
    nums = re.findall(r"\d+", stats_line)
    failures, errors = nums[1], nums[2]
    
    return int(failures) + int(errors)

if __name__ == '__main__':    
    parser = argparse.ArgumentParser(description="Compare rev pairs and triggered tests")
    parser.add_argument("--work_dir", required=True)
    parser.add_argument("--project_name", required=True)
    parser.add_argument("--project_id", required=True)
    parser.add_argument("--repo_url", required=True)
    
    args = parser.parse_args()
    
    work_dir, project_name, project_id, repo_url = args.work_dir, args.project_name, args.project_id, args.repo_url
    project_work_dir = "{work_dir}/framework/projects/{project_id}".format(work_dir=work_dir, project_id=project_id)
    rev_pair_path = "{work_dir}/rev_pairs".format(work_dir=work_dir)
    active_bug_path = "{project_work_dir}/active-bugs.csv".format(project_work_dir=project_work_dir)
    trigger_tests_path = "{project_work_dir}/trigger_tests".format(project_work_dir=project_work_dir)
    failing_tests_path = "{project_work_dir}/failing_tests".format(project_work_dir=project_work_dir)

    # Get all the bugs in the trigger_tests
    trigger_tests = [int(f) for f in listdir(trigger_tests_path) if isfile(join(trigger_tests_path, f))]

    # Get all the failing tests hash
    failing_tests = [f for f in listdir(failing_tests_path) if isfile(join(failing_tests_path, f))]
    
    # Get a list of bug ids in the rev pairs
    rev_pairs_df = pd.read_csv(rev_pair_path)
    candidates = rev_pairs_df["version_id"].tolist()
    
    # Go to active bugs and find the fixed versions
    active_bugs_df = pd.read_csv(active_bug_path)
    active_bugs_dic = {}
    for _, row in active_bugs_df.iterrows():
        active_bugs_dic[row["bug.id"]] = row["revision.id.fixed"]
        
    # Set up tmp repository
    subprocess.call("rm -rf {project_name}".format(project_name=project_name), shell=True, cwd="/tmp")
    subprocess.call("git clone {repo_url}".format(repo_url=repo_url), shell=True, cwd="/tmp")
    
    output = []   
    for rev in candidates:
        if rev not in trigger_tests:
            fixed_version = active_bugs_dic[rev]
            if fixed_version not in failing_tests:
                output.append("(Warning) Manually Inspect: Bug {rev} is not in trigger test but tests didn't fail.".format(rev=rev))
                continue
            failing_tests_count = get_bugs_in_file("{failing_tests_path}/{fixed_version}".format(failing_tests_path=failing_tests_path, fixed_version=fixed_version))
            repo_test_count = get_bugs_in_repo(fixed_version, project_name)
            if repo_test_count == -1:
                output.append("(Warning) Manually Inspect: Bug {rev} might have dependency issues.".format(rev=rev))
                continue
            if failing_tests_count > repo_test_count:
                output.append("(Warning) Manually Inspect: Bug {rev} contains more errors in failing_tests than it's supposed to.".format(rev=rev))
                continue 
            
    for o in output:
        print(o)
"""Shared Git/manual coordinator with lifecycle-wide interruption handling."""
import os
import sys

from . import containers, execution, preflight, qa, reports


def dispatch(root, run, env):
    execution.phase("qa")
    try:
        with (run / "runner.log").open("wb") as log:
            code = execution.run(["lefthook", "run", "qa-checks"], cwd=root,
                                 env=env, stdout=log, stderr=log).returncode
        return code, [], False
    except OSError as exc:
        return None, [f"Cannot launch Lefthook: {exc}"], False


def pre_push(stream, env=None, mode="git"):
    if execution.CURRENT is None:
        with execution.Session():
            return pre_push(stream, env, mode)
    session = execution.CURRENT
    env = dict(os.environ if env is None else env)
    run = initial = root = None
    started = reports.utc_now().isoformat()
    try:
        execution.phase("entry")
        execution.phase("environment")
        preflight.environment(env)
        execution.phase("git-root")
        root = preflight.root_directory()
        if mode == "git":
            execution.phase("input")
            record = preflight.updates(root, stream)
            if record is None:
                execution.phase("return")
                return 0
            execution.phase("checkout")
            preflight.checkout(root, record)
        elif mode == "manual":
            execution.phase("checkout")
            preflight.clean(root)
        else:
            raise ValueError("Invalid invocation mode")
        execution.phase("runtime")
        template = preflight.runtime(root)
        execution.phase("allocation")
        run = reports.allocate(root)
        if isinstance(template, dict):
            containers.configure(run, template)
        execution.phase("initial-publication")
        initial = reports.initial_summary(run, started, mode)
        env.update(QA_HOOKS_RUN_DIR=str(run), QA_HOOKS_EXECUTION_ID=run.name)
        code, errors, interrupted = dispatch(root, run, env)
        containers.cleanup(root, run, session)
        errors.extend(session.errors)
        summary = reports.finalize(run, initial, code, errors, interrupted)
        reports.terminal(run, summary)
        execution.phase("return")
        return summary["exit_code"]
    except execution.Interrupted:
        session.teardown()
        run = run or session.run_dir
        if run:
            reports.directory(run, "jobs", create=True)
            initial = initial or reports.initial_summary(run, started, mode)
            summary = reports.finalize(run, initial, None,
                [f"Interrupted by signal {session.number}", *session.errors], True)
            reports.terminal(run, summary)
        else:
            print(f"Pre-push interrupted by signal {session.number} during {session.phase_name}.",
                  file=sys.stderr)
            for error in session.errors:
                print(f"Cleanup failure: {error}", file=sys.stderr)
        return 1
    except (preflight.Rejected, OSError, ValueError, RuntimeError) as exc:
        if session.children:
            session.teardown()
        elif run:
            containers.cleanup(root, run, session)
        if run:
            reports.directory(run, "jobs", create=True)
            initial = initial or reports.initial_summary(run, started, mode)
            session.finishing = True
            summary = reports.finalize(run, initial, None, [str(exc), *session.errors])
            reports.terminal(run, summary)
            return 1
        raise


def main(args=None):
    args = sys.argv[1:] if args is None else args
    try:
        if len(args) == 3 and args[0] == "boundary":
            mode = args[1]
            marker = os.environ.get("QA_HOOKS_GIT_PUSH", "")
            if mode not in ("git", "manual") or marker not in ("", "1") or (mode == "git") != (marker == "1"):
                raise ValueError("Invalid Git/manual launcher context")
            return execution.boundary(mode, int(args[2]))
        with execution.Session() as session:
            if args and args[0] == "pre-push" and len(args) in (1, 2, 3):
                mode = args[1] if len(args) == 2 else "git"
                return pre_push(sys.stdin, mode=mode)
            if len(args) == 2 and args[0] == "check":
                try:
                    execution.phase("entry")
                    return qa.check(preflight.root_directory(), args[1])
                except execution.Interrupted:
                    session.teardown()
                    print(f"Validation interrupted during {session.phase_name}", file=sys.stderr)
                    return 1
            print("Usage: tools/git-hooks boundary <git|manual> <frontend-pid> | check <id>",
                  file=sys.stderr)
            return 2
    except (preflight.Rejected, OSError, ValueError, RuntimeError) as exc:
        print(f"Pre-push rejected: {exc}", file=sys.stderr)
        return 1

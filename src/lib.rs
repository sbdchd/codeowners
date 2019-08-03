use codeowners as rs_codeowners;
use pyo3::prelude::*;

#[pyclass]
struct CodeOwners {
    owners: codeowners::Owners,
}

#[pymethods]
impl CodeOwners {
    #[new]
    fn new(obj: &PyRawObject, text: String) {
        let owners = rs_codeowners::from_reader(text.as_bytes());
        obj.init({ CodeOwners { owners } });
    }

    pub fn of(&self, file_path: String) -> PyResult<Option<Vec<(String, String)>>> {
        Ok(match self.owners.of(file_path) {
            Some(o) => Some(convert_owner_to_tuple(o)),
            None => None,
        })
    }
}

#[pymodule]
fn codeowners(_py: Python<'_>, m: &PyModule) -> PyResult<()> {
    m.add_class::<CodeOwners>()?;

    Ok(())
}

const USERNAME: &str = "USERNAME";
const TEAM: &str = "TEAM";
const EMAIL: &str = "EMAIL";

fn convert_owner_to_tuple(owners: &[rs_codeowners::Owner]) -> Vec<(String, String)> {
    owners
        .iter()
        .map(|o| match o {
            rs_codeowners::Owner::Username(s) => (USERNAME.to_string(), s.to_string()),
            rs_codeowners::Owner::Team(s) => (TEAM.to_string(), s.to_string()),
            rs_codeowners::Owner::Email(s) => (EMAIL.to_string(), s.to_string()),
        })
        .collect()
}

#[cfg(test)]
mod tests {
    use super::*;

    const EXAMPLE: &str = r"# This is a comment.
# Each line is a file pattern followed by one or more owners.
# These owners will be the default owners for everything in
# the repo. Unless a later match takes precedence,
# @global-owner1 and @global-owner2 will be requested for
# review when someone opens a pull request.
*       @global-owner1 @global-owner2
# Order is important; the last matching pattern takes the most
# precedence. When someone opens a pull request that only
# modifies JS files, only @js-owner and not the global
# owner(s) will be requested for a review.
*.js    @js-owner
# You can also use email addresses if you prefer. They'll be
# used to look up users just like we do for commit author
# emails.
*.go docs@example.com
# In this example, @doctocat owns any files in the build/logs
# directory at the root of the repository and any of its
# subdirectories.
/build/logs/ @doctocat
# The `docs/*` pattern will match files like
# `docs/getting-started.md` but not further nested files like
# `docs/build-app/troubleshooting.md`.
docs/*  docs@example.com
# In this example, @octocat owns any file in an apps directory
# anywhere in your repository.
apps/ @octocat
# In this example, @doctocat owns any file in the `/docs`
# directory in the root of your repository.
/docs/ @doctocat
";

    #[test]
    fn codeowners() {
        let owners = rs_codeowners::from_reader(EXAMPLE.as_bytes());
        assert_eq!(
            owners.of("foo.js"),
            Some(&vec![rs_codeowners::Owner::Username("@js-owner".into())])
        );
    }

    #[test]
    fn converting_from_enum_to_tuple() {
        let inputs = vec![
            rs_codeowners::Owner::Username("a".into()),
            rs_codeowners::Owner::Team("b".into()),
            rs_codeowners::Owner::Email("c".into()),
        ];
        let expected = vec![
            (USERNAME.to_string(), "a".to_string()),
            (TEAM.to_string(), "b".to_string()),
            (EMAIL.to_string(), "c".to_string()),
        ];

        assert_eq!(convert_owner_to_tuple(&inputs), expected);
    }
}

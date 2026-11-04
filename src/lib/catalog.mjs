export function filterProjects(projects, query = '', category = 'all') {
  const terms = query.normalize('NFKC').trim().toLocaleLowerCase().split(/\s+/).filter(Boolean);
  return projects.filter(project => {
    const text = [project.name, project.description, ...(project.tags || []), ...(project.keywords || [])].join(' ').toLocaleLowerCase();
    return (category === 'all' || project.category === category) && terms.every(term => text.includes(term));
  });
}

export function sitePath(path = '', base = '/') {
  return `${base.replace(/\/$/, '')}/${path.replace(/^\//, '')}`;
}

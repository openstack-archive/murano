script "install" do
  interpreter "bash"
  user "root"
  cwd "/opt"
  code <<-EOH
  echo test install
  EOH
end

node.normal['test']['action_test'] = "install"